#!/usr/bin/env python3
"""Build TMLink applications and protocol servers from a TOML file."""

import os
import shlex

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from ApplicationServer import (
    GenericApplication,
    RTPClientApplication,
    RTPServerApplication,
    VNCApplication,
)


class ConfiguredApplication(GenericApplication):
    """A configured process with TMLink metadata and templated arguments."""

    def __init__(self, command, uri, display=None, environment=None):
        GenericApplication.__init__(
            self, command, uri, display=display, environment=environment)


class ConfiguredApplicationList:
    """Create protocol infrastructure and applications described by TOML."""

    def __init__(self, server, host_address, config_path):
        self.server = server
        self.host = host_address
        self.config_path = config_path
        self.config_dir = os.path.dirname(os.path.abspath(config_path))
        self.config = self._load()
        self.targets = {}
        self.applications = []

        self._create_targets()
        self._create_applications()

    def _load(self):
        with open(self.config_path, 'rb') as config_file:
            return tomllib.load(config_file)

    def _section(self, name):
        section = self.config.get(name, {})
        if not isinstance(section, dict):
            raise ValueError("'{}' must be a TOML table".format(name))
        return section

    def _create_targets(self):
        targets = self._section('targets')
        defaults = {
            'vnc': {
                'enabled': True,
                'screen': 1,
                'port': 5901,
            },
            'rtp': {
                'enabled': True,
                'port': 12345,
                'audio_source': 'system',
                'sink_name': 'tmlink_rtp_sink',
                'gst_launch_fallback': False,
            },
        }

        for name, default in defaults.items():
            settings = dict(default)
            settings.update(targets.get(name, {}))
            if settings.get('enabled', True):
                self._create_target(name, settings)

        for name, settings in targets.items():
            if name not in defaults and settings.get('enabled', True):
                self._create_target(name, settings)

    def _create_target(self, name, settings):
        protocol = settings.get('protocol', name).upper()
        if protocol == 'VNC':
            target = VNCApplication(
                self.host,
                screen_id=settings.get('screen'),
                port=settings.get('port'),
            )
        elif protocol == 'RTP':
            direction = settings.get('direction', 'out')
            if direction == 'in':
                target = RTPClientApplication(
                    self.host,
                    port=settings.get('port', 12346),
                    stream_type=settings.get('stream_type'),
                    sink_device=settings.get('sink_device', 'hw:1,1,1'),
                )
            else:
                target = RTPServerApplication(
                    self.host,
                    audio_source=settings.get('audio_source', 'system'),
                    sink_name=settings.get('sink_name', 'tmlink_rtp_sink'),
                    gst_launch_fallback=settings.get(
                        'gst_launch_fallback', False),
                    port=settings.get('port', 12345),
                )
        else:
            raise ValueError("Unsupported target protocol: {}".format(protocol))

        self._apply_metadata(target, settings)
        target.name = settings.get('name', name)
        target.autoLaunch = settings.get('auto_launch', True)
        target.noTerminate = settings.get('no_terminate', True)
        target.noListing = settings.get('no_listing', True)
        self.targets[name] = target
        self.server.addApplication(target)

    def _template_values(self, target=None):
        values = {
            'host': self.host,
            'config_dir': self.config_dir,
        }
        if target is not None:
            values.update({
                'uri': target.uri,
                'vnc_uri': target.uri if target.protocolID == 'VNC' else '',
                'rtp_uri': target.uri if target.protocolID == 'RTP' else '',
                'port': target.port,
                'display': getattr(target, 'screenID', ''),
                'display_number': getattr(target, 'screenID', ''),
                'sink_name': getattr(target, 'sink_name', ''),
                'audio_source': getattr(target, 'audio_source', ''),
                'sink_device': getattr(target, 'sink_device', ''),
                'stream_type': getattr(target, 'stream_type', ''),
            })
        for name, target in self.targets.items():
            values['{}_uri'.format(name)] = target.uri
            values['{}_port'.format(name)] = target.port
            values['{}_display'.format(name)] = getattr(
                target, 'screenID', '')
            values['{}_sink_name'.format(name)] = getattr(
                target, 'sink_name', '')
            values['{}_audio_source'.format(name)] = getattr(
                target, 'audio_source', '')
            values['{}_sink_device'.format(name)] = getattr(
                target, 'sink_device', '')
            values['{}_stream_type'.format(name)] = getattr(
                target, 'stream_type', '')
        return values

    def _render(self, value, target=None):
        if not isinstance(value, str):
            return value
        values = self._template_values(target)
        return value.format(**values)

    def _render_command(self, command, target=None):
        if isinstance(command, str):
            command = shlex.split(command)
        if not isinstance(command, list) or not command:
            raise ValueError("application command must be a non-empty array")
        return [self._render(item, target) for item in command]

    def _create_applications(self):
        applications = self.config.get('applications', [])
        if not isinstance(applications, list):
            raise ValueError("'applications' must be an array of tables")

        for settings in applications:
            if not isinstance(settings, dict):
                raise ValueError("each application must be a TOML table")
            settings = dict(settings)
            target_name = settings.get('target')
            target = self.targets.get(target_name) if target_name else None
            protocol = settings.get('protocol', 'VNC').upper()
            settings.setdefault('protocolID', protocol)
            if target is None:
                target = next(
                    (item for item in self.targets.values()
                     if item.protocolID == protocol),
                    None)
            if target is None:
                raise ValueError(
                    "no {} target available for application '{}'".format(
                        protocol, settings.get('name', '<unnamed>')))

            if 'command' in settings:
                command_spec = settings['command']
            else:
                command_spec = [settings['executable']] + settings.get(
                    'arguments', [])
            command = self._render_command(command_spec, target)
            display = settings.get(
                'display', getattr(target, 'screenID', None))
            if display is not None:
                display = self._render(display, target)
            environment = {
                key: self._render(value, target)
                for key, value in settings.get('environment', {}).items()
            }
            app = ConfiguredApplication(
                command,
                target.uri,
                display=display,
                environment=environment,
            )
            self._apply_metadata(app, settings)
            app.name = settings.get('name', 'Configured application')
            app.description = settings.get('description')
            app.autoLaunch = settings.get('auto_launch', False)
            app.noTerminate = settings.get('no_terminate', False)
            app.noListing = settings.get('no_listing', False)
            self.server.addApplication(app)
            self.applications.append(app)

    @staticmethod
    def _apply_metadata(app, settings):
        fields = (
            'protocolID', 'format', 'direction', 'appCategory',
            'appTrustLevel', 'displayCategory', 'displayTrustLevel',
            'audioType', 'audioCategory', 'audioTrustLevel',
            'resourceStatus', 'iconURL', 'iconWidth', 'iconHeight',
            'iconDepth',
        )
        for field in fields:
            if field in settings:
                setattr(app, field, settings[field])
        for field in ('hasAppInfo', 'hasDisplay', 'hasAudio'):
            if field in settings:
                setattr(app, field, settings[field])

        if settings.get('protocolID', '').upper() == 'RTP':
            app.hasDisplay = settings.get('hasDisplay', False)
            app.hasAudio = settings.get('hasAudio', True)
