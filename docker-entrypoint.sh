#!/bin/bash
set -e

SSH_USER=${SSH_USER:-developer}
SSH_HOME="/home/${SSH_USER}"
SSH_DIR="${SSH_HOME}/.ssh"
HOST_KEY_PATH=${HOST_AUTH_KEYS_PATH:-"/authorized_keys"}

# ensure ssh runtime dir
mkdir -p /var/run/sshd

# create user if missing
id "${SSH_USER}" >/dev/null 2>&1 || useradd -m -s /bin/bash "${SSH_USER}"

# if a host-mounted authorized_keys exists, copy it into the user's .ssh so we can set perms
if [ -f "${HOST_KEY_PATH}" ]; then
  mkdir -p "${SSH_DIR}"
  cp -f "${HOST_KEY_PATH}" "${SSH_DIR}/authorized_keys"
  chown -R "${SSH_USER}:${SSH_USER}" "${SSH_DIR}"
  chmod 700 "${SSH_DIR}"
  chmod 600 "${SSH_DIR}/authorized_keys"
fi

# enforce key-only auth
sed -ri 's/^#?PasswordAuthentication\s+.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin no/' /etc/ssh/sshd_config

exec /usr/sbin/sshd -D