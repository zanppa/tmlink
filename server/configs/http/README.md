# HTTP Server

The preferred HTTP server is the standalone Python service included in the
server directory. It uses only the Python standard library and is independent
of both the application server and the UPnP server.

## Built-in Python server

Static files are kept in `server/http/`. Add icons under that directory, then
start the service from `server/`:

```sh
sh launch_http.sh
```

The defaults serve `server/http/` on `192.168.10.1:8000`. The bind address,
port, and document root can be overridden with command-line options:

```sh
python3 http_server.py \
    --bind 192.168.10.1 \
    --port 8000 \
    --root http
```

The launcher also accepts the `TMLINK_HTTP_BIND`, `TMLINK_HTTP_PORT`, and
`TMLINK_HTTP_ROOT` environment variables. It serves files using HTTP `GET`
and `HEAD`, rejects directory listings and write methods, and should be bound
to the USB-network address rather than all interfaces.

For example, the UPnP device icon URL can be:

```text
http://192.168.10.1:8000/icon.png
```

## Alternative: webfsd

The existing `webfsd.conf` is retained as an alternative for installations
that already use the external `webfs` package. It is no longer the
recommended setup; the built-in Python server avoids an additional package
and keeps the static-file service in the TMLink server tree.
