#!/bin/sh
PYTHON=/usr/bin/python3
APP_DIR=/usr/share/vpngate-gtk

PYTHONPATH="$APP_DIR" exec "$PYTHON" "$APP_DIR/main.py" "$@"
