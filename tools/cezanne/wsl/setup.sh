#!/bin/bash
# setup único da distro WSL "aero-runners" (Ubuntu 24.04), como root, com o repo acessível.
# Prepara: systemd, usuário dasher (uid 1000, igual ao bare metal), docker.io e gh da mesma série
# do Ubuntu do disco, e /opt/aero-wsl com up/down e o aero-poweroff.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
[ "$(id -u)" = 0 ] || { echo "rode como root" >&2; exit 1; }

if id dasher >/dev/null 2>&1; then
    [ "$(id -u dasher)" = 1000 ] || { echo "dasher existe com uid $(id -u dasher), precisa ser 1000" >&2; exit 1; }
else
    if getent passwd 1000 >/dev/null; then
        echo "uid 1000 já é $(getent passwd 1000 | cut -d: -f1); crie a distro sem usuário padrão ou renomeie" >&2; exit 1
    fi
    useradd -u 1000 -U -m -s /bin/bash dasher
fi

cat > /etc/wsl.conf <<'EOF'
[boot]
systemd=true

[user]
default=dasher

[automount]
options = "metadata"
EOF

apt-get update
apt-get install -y docker.io gh python3 rsync
usermod -aG docker dasher
# docker só sobe depois do bind de /var/lib/docker (up.sh)
systemctl disable docker.service docker.socket 2>/dev/null || true

install -d /opt/aero-wsl
install -m755 "$here/up.sh" "$here/down.sh" /opt/aero-wsl/
install -m755 "$here/../aero-poweroff" /opt/aero-wsl/aero-poweroff
echo "ok. No Windows: wsl --terminate aero-runners (para valer o systemd) e depois .\\aero-wsl.ps1 up"
