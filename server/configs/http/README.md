# HTTP Server

## Introduction
HTTP server is used to serve e.g. icons and other static content.

## Installation
`sudo apt-get install webfs`

Also we need to create a base directory, default in Raspbian is:
`/var/www/html`

Run
```
sudo mkdir -p /var/www/html
sudo chown -R www-data.www-data /var/www
```

## Configuration
The default configuration is almost good, we just change that the server 
binds to the USB interface.

Copy/merge the included `webfsd.conf` to `/etc/webfsd.conf`. Note: at this 
point the server binds to all interfaces, this will change later.

