# TMLink HTTP content

This directory is the document root for the standalone `server/http_server.py`
service. Put device icons, application icons, and other public static files
here.

For example:

```text
http/
├── applications/
│   ├── audio-out.png
│   └── vnc.png
└── device/
    └── logo.png
```

The server does not expose directory listings. A file is available at the
same path below the configured HTTP root, for example:

```text
http://192.168.10.1:8000/applications/vnc.png
```

The directory is intentionally independent of `ApplicationServer.py` and the
UPnP server.
