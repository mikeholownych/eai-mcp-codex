#!/bin/sh

# This script is the entrypoint for the Vault Agent container.
# It reads the VAULT_ROLE_ID and VAULT_SECRET_ID from Docker secrets
# and passes them to the vault agent command.

# Read VAULT_ROLE_ID from Docker secret file
if [ -f "${VAULT_ROLE_ID_FILE}" ]; then
  export VAULT_ROLE_ID=$(cat "${VAULT_ROLE_ID_FILE}")
  echo "VAULT_ROLE_ID loaded from file."
else
  echo "Error: VAULT_ROLE_ID_FILE not found or empty: ${VAULT_ROLE_ID_FILE}"
  exit 1
fi

# Read VAULT_SECRET_ID from Docker secret file
if [ -f "${VAULT_SECRET_ID_FILE}" ]; then
  export VAULT_SECRET_ID=$(cat "${VAULT_SECRET_ID_FILE}")
  echo "VAULT_SECRET_ID loaded from file."
else
  echo "Error: VAULT_SECRET_ID_FILE not found or empty: ${VAULT_SECRET_ID_FILE}"
  exit 1
fi

# Execute the vault agent command with the loaded credentials
echo "Starting vault agent with config /vault/agent-config.hcl"
echo "VAULT_ADDR: $VAULT_ADDR"
exec /bin/vault agent -config=/vault/agent-config.hcl
