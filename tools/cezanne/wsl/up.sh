#!/bin/bash
# dentro da distro aero-runners, como root: liga /home/dasher e /var/lib/docker do disco do Ubuntu
# (montado pelo Windows em /mnt/wsl/aero-sdc) e sobe docker + as mesmas units dos runners.
set -euo pipefail
MNT=/mnt/wsl/aero-sdc
UNITS=$(ls "$MNT"/etc/systemd/system/actions.runner.*.service 2>/dev/null | xargs -rn1 basename || true)

if [ "${1:-}" = "--status" ]; then
    findmnt -n /home/dasher /var/lib/docker || echo "binds não montados"
    for u in $UNITS; do printf '%s %s\n' "$u" "$(systemctl is-active "$u")"; done
    exit 0
fi

[ -d "$MNT/home/dasher/actions-runner-1" ] || { echo "disco não montado em $MNT (rode wsl --mount pelo aero-wsl.ps1)" >&2; exit 1; }
[ -n "$UNITS" ] || { echo "nenhuma unit de runner em $MNT/etc/systemd/system" >&2; exit 1; }

systemctl stop docker.service docker.socket 2>/dev/null || true
mkdir -p /var/lib/docker
findmnt -n /home/dasher >/dev/null || mount --bind "$MNT/home/dasher" /home/dasher
findmnt -n /var/lib/docker >/dev/null || mount --bind "$MNT/var/lib/docker" /var/lib/docker

for u in $UNITS; do
    install -m644 "$MNT/etc/systemd/system/$u" "/etc/systemd/system/$u"
done
systemctl daemon-reload
systemctl start docker.service
for u in $UNITS; do systemctl start "$u"; done
for u in $UNITS; do printf '%s %s\n' "$u" "$(systemctl is-active "$u")"; done
