#!/bin/bash
set -e

SSH_USER=${SSH_USER:-developer}
SSH_HOME="/home/${SSH_USER}"
SSH_DIR="${SSH_HOME}/.ssh"
HOST_KEY_PATH=${HOST_AUTH_KEYS_PATH:-"/authorized_keys"}
NOTEBOOKS_DIR=/workspace/app/notebooks
# allow multiple files (colon or comma separated) or fallback to single ENV_FILE
ENV_FILES=${ENV_FILES:-${ENV_FILE:-/workspace/.env}}

# ...existing code...

# ensure ssh runtime dir
mkdir -p /var/run/sshd

# create user if missing
id "${SSH_USER}" >/dev/null 2>&1 || useradd -m -s /bin/bash "${SSH_USER}"

# load env files (ENV_FILES can be colon- or comma-separated)
# export variables for the entrypoint and child processes, and prepare ~/.ssh/environment
mkdir -p "${SSH_DIR}"
TMP_ENV_FILE="$(mktemp)"
IFS=':,' read -ra EF <<< "$ENV_FILES"
for f in "${EF[@]}"; do
  if [ -n "$f" ] && [ -f "$f" ]; then
    # export vars for current process
    set -a
    # shellcheck disable=SC1090
    . "$f"
    set +a
    # append file contents to temporary environment file for ssh sessions
    cat "$f" >> "${TMP_ENV_FILE}"
    printf "\n" >> "${TMP_ENV_FILE}"
  fi
done
if [ -s "${TMP_ENV_FILE}" ]; then
  mv "${TMP_ENV_FILE}" "${SSH_DIR}/environment"
  chown "${SSH_USER}:${SSH_USER}" "${SSH_DIR}/environment"
  chmod 600 "${SSH_DIR}/environment"
else
  rm -f "${TMP_ENV_FILE}" || true
fi

# if a host-mounted authorized_keys exists, copy it into the user's .ssh so we can set perms
if [ -f "${HOST_KEY_PATH}" ]; then
  cp -f "${HOST_KEY_PATH}" "${SSH_DIR}/authorized_keys"
  chown -R "${SSH_USER}:${SSH_USER}" "${SSH_DIR}"
  chmod 700 "${SSH_DIR}"
  chmod 600 "${SSH_DIR}/authorized_keys"
fi

# ...existing code...

if [ -d "$NOTEBOOKS_DIR" ]; then
  chown -R ${SSH_USER:-developer}:${SSH_USER:-developer} "$NOTEBOOKS_DIR" || true
  chmod -R u+rwX,go+rX "$NOTEBOOKS_DIR" || true
fi

# enforce key-only auth and allow user environment to be loaded by sshd
sed -ri 's/^#?PasswordAuthentication\s+.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -ri 's/^#?PermitUserEnvironment\s+.*/PermitUserEnvironment yes/' /etc/ssh/sshd_config || echo "PermitUserEnvironment yes" >> /etc/ssh/sshd_config

exec /usr/sbin/sshd -D