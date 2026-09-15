#!/usr/bin/env python3
"""Small standalone HTTP server for TMLink static files."""

import argparse
import functools
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class StaticFileHandler(SimpleHTTPRequestHandler):
    """Serve files only; do not expose directory listings or write methods."""

    def list_directory(self, path):
        self.send_error(404, "Not Found")
        return None

    def do_POST(self):
        self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        self.send_error(405, "Method Not Allowed")

    def log_message(self, format_string, *args):
        print("{} - {}".format(self.address_string(), format_string % args))


def main():
    parser = argparse.ArgumentParser(
        description="Serve TMLink icons and other static files"
    )
    parser.add_argument(
        "-i",
        "--interface",
        "--bind",
        dest="bind",
        default="192.168.10.1",
        help="address to listen on",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="TCP port to listen on",
    )
    parser.add_argument(
        "-r",
        "--root",
        default=os.path.join(os.path.dirname(__file__), "http"),
        help="directory containing files to serve",
    )
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        parser.error("HTTP root does not exist: {}".format(root))

    handler = functools.partial(StaticFileHandler, directory=root)
    server = ThreadingHTTPServer((args.bind, args.port), handler)

    print("Serving {} on http://{}:{}/".format(root, args.bind, args.port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
