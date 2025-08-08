pid_file = "/var/run/vault-agent-pid"

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id = "${VAULT_ROLE_ID}"
      secret_id = "${VAULT_SECRET_ID}"
    }
  }

  sink "file" {
    config = {
      path = "/vault/secrets/token"
    }
  }
}

template {
  source = "/vault/secrets/auth_config.ctmpl"
  destination = "/vault/secrets/auth_config.env"
  command = "/bin/sh -c \"kill -HUP 1\""
}

