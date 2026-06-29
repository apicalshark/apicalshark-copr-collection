#!/bin/sh
PYTHON=/usr/bin/python3
APP_DIR=/usr/share/vpngate-gtk

for pyc in "$APP_DIR"/__pycache__/main.*.pyc "$APP_DIR"/main.*.pyc; do
  if [ -f "$pyc" ]; then
    exec "$PYTHON" "$pyc" "$@"
  fi
done

# exec "$PYTHON" "$APP_DIR/main.py" "$@"
