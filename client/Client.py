#!/usr/bin/env python3
"""TMLink client for discovering and controlling applications on one server."""

import sys
import os
import subprocess
import curses
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import upnpclient


class Server:
    """UPnP application server and the applications it exposes."""

    SERVICE_NAMES = ("TmApplicationServer", "TmApplicationServer1")
    REQUIRED_ACTIONS = (
        "GetApplicationList",
        "LaunchApplication",
        "TerminateApplication",
        "GetApplicationStatus",
    )

    def __init__(self, device, profile_id=0):
        self.device = device
        self.profile_id = profile_id
        self.service = self._find_application_service()
        self.applications = {}

        missing = [
            action for action in self.REQUIRED_ACTIONS
            if action not in self.service.action_map
        ]
        if missing:
            raise RuntimeError(
                "Application server is missing actions: {}".format(
                    ", ".join(missing)
                )
            )

        self.refresh_applications()

    @classmethod
    def discover(cls, timeout=5, profile_id=0):
        """Discover TMLink servers and return one ``Server`` per device."""
        devices = upnpclient.discover(timeout)
        return [
            cls(device, profile_id)
            for device in devices
            if device.device_type == "urn:schemas-upnp-org:device:TmServerDevice:1"
        ]

    def _find_application_service(self):
        service_name = next(
            (name for name in self.SERVICE_NAMES if name in self.device.service_map),
            None,
        )
        if service_name is None:
            raise RuntimeError("Application server service not found")
        return self.device.service_map[service_name]

    def refresh_applications(self):
        """Fetch and parse the application list from the server."""
        response = self.service.GetApplicationList(
            AppListingFilter="", ProfileID=self.profile_id
        )
        root = ET.fromstring(response["AppListing"])
        self.applications = {}

        for app_element in root.findall("app"):
            app = Application.from_xml(self, app_element)
            self.applications[app.app_id] = app

        return list(self.applications.values())

    def get_application(self, app_id):
        """Return an application by ID, refreshing the list if necessary."""
        app_id = str(app_id)
        if app_id not in self.applications:
            self.refresh_applications()
        try:
            return self.applications[app_id]
        except KeyError:
            raise ValueError("Unknown application ID: {}".format(app_id))

    def launch_application(self, app_id):
        """Launch an application on the server and return its URI."""
        app = self.get_application(app_id)
        return self.service.LaunchApplication(
            AppID=app.app_id, ProfileID=self.profile_id
        )["AppURI"]

    def terminate_application(self, app_id):
        """Terminate an application on the server."""
        app = self.get_application(app_id)
        response = self.service.TerminateApplication(
            AppID=app.app_id, ProfileID=self.profile_id
        )
        return response.get("TerminationResult", response)

    def get_application_status(self, app_id):
        """Return the server's XML status response for an application."""
        app = self.get_application(app_id)
        response = self.service.GetApplicationStatus(
            AppID=app.app_id, ProfileID=self.profile_id
        )
        return response.get("AppStatus", response)

    def stop_all(self):
        """Stop all locally launched application clients."""
        for app in self.applications.values():
            if app.server_running or app.process is not None:
                app.stop()


class Application:
    """Application metadata and the local client connected to that application."""

    protocol = None

    def __init__(
        self,
        server,
        app_id,
        name="",
        uri="",
        formats=None,
        direction=None,
        protocol=None,
        metadata=None,
    ):
        self.server = server
        self.app_id = str(app_id)
        self.name = name
        self.uri = uri
        self.formats = formats or []
        self.direction = direction
        if protocol is not None:
            self.protocol = protocol
        self.metadata = metadata or {}
        self.process = None
        self.server_running = False
        self.run_status = "Unknown"

    @classmethod
    def from_xml(cls, server, app_element):
        """Create the appropriate application subclass from app-list XML."""
        app_id = app_element.findtext("appID", "")
        protocol = app_element.findtext("./remotingInfo/protocolID", "").upper()
        app_class = {
            "VNC": VNCApplication,
            "RTP": RTPApplication,
        }.get(protocol, GenericApplication)

        formats_text = app_element.findtext("./remotingInfo/format", "")
        formats = [value.strip() for value in formats_text.split(",") if value.strip()]
        return app_class(
            server=server,
            app_id=app_id,
            name=app_element.findtext("name", ""),
            formats=formats,
            direction=app_element.findtext("./remotingInfo/direction"),
            protocol=protocol,
            metadata={
                "provider_name": app_element.findtext("providerName", ""),
                "description": app_element.findtext("description", ""),
            },
        )

    def launch(self):
        """Launch the server application and its local protocol client."""
        if self.is_running():
            return self.uri

        self.uri = self.server.launch_application(self.app_id)
        self.server_running = True
        try:
            self.process = self._launch_client()
        except (OSError, ValueError, NotImplementedError):
            self.server.terminate_application(self.app_id)
            self.server_running = False
            raise
        return self.uri

    def stop(self):
        """Stop the local client and then terminate the server application."""
        stopped = False
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                stopped = True
            self.process = None

        termination_result = False
        if self.server_running:
            termination_result = self.server.terminate_application(self.app_id)
            self.server_running = False
        return stopped or termination_result

    def status(self):
        """Query the current application status from the server."""
        current_status = self.server.get_application_status(self.app_id)
        current_status = ET.fromstring(current_status)

        if current_status.tag != "appStatusList":
            return "Unknown"
        status_app_id = self.run_status = current_status.findtext("./appStatus/appID", "")
        if not status_app_id == self.app_id:
            return "Unknown"

        self.run_status = current_status.findtext("./appStatus/status/statusType", "Unknown")
        return self.run_status

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def _launch_client(self):
        raise NotImplementedError


class VNCApplication(Application):
    """Application whose server URI is consumed by the bundled VNC viewer."""

    protocol = "VNC"

    def _launch_client(self):
        uri = urlparse(self.uri)
        if uri.hostname is None or uri.port is None:
            raise ValueError("Invalid VNC URI: {}".format(self.uri))

        command = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "vncviewer", "vncviewer_ml.py"),
            "--host={}".format(uri.hostname),
            "--display={}".format(uri.port - 5900),
        ]
        return self._start_process(command)

    def _start_process(self, command):
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class RTPApplication(Application):
    """Application whose server URI is consumed by the RTP client."""

    protocol = "RTP"

    def _launch_client(self):
        uri = urlparse(self.uri)
        if uri.hostname is None or uri.port is None:
            raise ValueError("Invalid RTP URI: {}".format(self.uri))

        command = [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "RTPClient.py"),
            uri.hostname,
            str(uri.port),
        ]
        if self.formats:
            command.extend(("-t", self.formats[0]))
        return self._start_process(command)

    def _start_process(self, command):
        return subprocess.Popen(command)


class GenericApplication(Application):
    """Fallback application for protocols without a local client implementation."""

    protocol = "GENERIC"

    def _launch_client(self):
        raise NotImplementedError(
            "No local client is implemented for protocol {}".format(
                self.protocol or "unknown"
            )
        )


def select_server(servers):
    """Select one server interactively."""
    if not servers:
        return None
    if len(servers) == 1:
        print("Using server {}".format(servers[0].device.location))
        return servers[0]

    print("Select server to use")
    for number, server in enumerate(servers):
        print("{:02d}: {}".format(number, server.device.location))

    while True:
        try:
            selected = int(input("> "))
        except (TypeError, ValueError):
            print("Erroneous selection, give number")
            continue
        if 0 <= selected < len(servers):
            return servers[selected]
        print("Give number between 0 and {}".format(len(servers) - 1))


def _menu(stdscr, title, items, status=""):
    """Display a scrollable menu and return the selected item index."""
    selected = 0
    top = 0
    height, width = stdscr.getmaxyx()
    visible_count = max(1, height - 5)

    while True:
        height, width = stdscr.getmaxyx()
        visible_count = max(1, height - 5)
        if selected < top:
            top = selected
        elif selected >= top + visible_count:
            top = selected - visible_count + 1

        stdscr.erase()
        stdscr.addnstr(0, 0, title, max(0, width - 1), curses.A_BOLD)
        if items:
            for row, item in enumerate(items[top:top + visible_count], start=2):
                index = top + row - 2
                attribute = curses.A_REVERSE if index == selected else curses.A_NORMAL
                stdscr.addnstr(
                    row,
                    0,
                    "{} {}".format(">" if index == selected else " ", item),
                    max(0, width - 1),
                    attribute,
                )
        else:
            stdscr.addnstr(2, 0, "No items available", max(0, width - 1))

        if status:
            stdscr.addnstr(height - 2, 0, status, max(0, width - 1))
        stdscr.addnstr(
            height - 1,
            0,
            "Up/Down: move  Enter: select  Esc/q: back",
            max(0, width - 1),
            curses.A_DIM,
        )
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and items:
            selected = (selected - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")) and items:
            selected = (selected + 1) % len(items)
        elif key in (curses.KEY_ENTER, 10, 13) and items:
            return selected
        elif key in (27, ord("q")):
            return None


def _show_message(stdscr, title, message):
    """Show a possibly multiline message until the user presses a key."""
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.addnstr(0, 0, title, max(0, width - 1), curses.A_BOLD)
    for row, line in enumerate(str(message).splitlines(), start=2):
        if row >= height - 2:
            break
        stdscr.addnstr(row, 0, line, max(0, width - 1))
    stdscr.addnstr(
        height - 1, 0, "Press any key to return", max(0, width - 1), curses.A_DIM
    )
    stdscr.refresh()
    stdscr.getch()


def _run_curses(stdscr, servers):
    """Run the interactive client using only the standard curses module."""
    curses.curs_set(0)
    stdscr.keypad(True)

    if len(servers) == 1:
        server = servers[0]
    else:
        server_index = _menu(
            stdscr,
            "Select TMLink server",
            [server.device.location for server in servers],
        )
        if server_index is None:
            return
        server = servers[server_index]

    status = "Select an application"
    while True:
        applications = list(server.applications.values())
        app_index = _menu(
            stdscr,
            "Applications on {}".format(server.device.location),
            [
                "{} [{}]".format(app.name or "(unnamed)", app.protocol or "unknown")
                for app in applications
            ],
            status,
        )
        if app_index is None:
            return

        app = applications[app_index]
        action_index = _menu(
            stdscr,
            "{} ({})".format(app.name or "(unnamed)", app.protocol or "unknown"),
            ["Launch", "Stop", "Query status", "Back"],
        )
        if action_index is None or action_index == 3:
            status = "Select an application"
            continue

        try:
            if action_index == 0:
                uri = app.launch()
                status = "Launched: {}".format(uri)
            elif action_index == 1:
                status = "Stopped: {}".format(app.stop())
            else:
                _show_message(stdscr, "Status for {}".format(app.name), app.status())
                status = "Select an application"
        except (OSError, RuntimeError, ValueError, NotImplementedError) as error:
            _show_message(stdscr, "Operation failed", error)
            status = "Operation failed: {}".format(error)


def run_cli():
    timeout = 2
    print("Searching devices for {} seconds...".format(timeout))
    try:
        servers = Server.discover(timeout)
    except RuntimeError as error:
        print("ERROR: {}".format(error))
        return 1
    print("Search done")

    if not servers:
        print("No servers found")
        return 0

    try:
        curses.wrapper(_run_curses, servers)
    finally:
        for server in servers:
            server.stop_all()

    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
