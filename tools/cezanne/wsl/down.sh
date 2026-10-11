#!/bin/bash
# dentro da distro aero-runners, como root: encerra os runners pelo aero-poweroff (cancela e comenta
# jobs em andamento), para o docker e desfaz os binds, deixando o disco pronto para o wsl --unmount.
set -euo pipefail
if findmnt -n /home/dasher >/dev/null; then
    # falha aqui não pode impedir parar o docker e desfazer os binds
    AERO_RUNNERS_DIR=/home/dasher /opt/aero-wsl/aero-poweroff --yes --no-reboot \
        || echo "AVISO: aero-poweroff saiu com $?; seguindo para parar o docker" >&2
fi
systemctl stop docker.service docker.socket 2>/dev/null || true
sync
findmnt -n /var/lib/docker >/dev/null && umount /var/lib/docker
findmnt -n /home/dasher >/dev/null && umount /home/dasher
echo "binds desfeitos"
