#!/usr/bin/env bash

if [ -f /ssh/config ]; then
    cp /ssh/config /home/fabric/.ssh/
fi

if [ -f /ssh/id_ed25519 ]; then
    cp /ssh/id_ed25519 /home/fabric/.ssh/
fi

chown -R fabric:fabric /home/fabric/.ssh

chmod 600 /home/fabric/.ssh/id_ed25519

if [ $# -eq 0 ]; then
    tail -f /dev/null
else
    exec "$@"
fi
