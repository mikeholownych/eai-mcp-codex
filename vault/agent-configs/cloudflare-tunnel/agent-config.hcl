
# Vault Agent Configuration for Cloudflare Tunnel Service
# This configuration instructs the agent to authenticate using AppRole
# and to render secrets from Vault to a file.

pid_file = "/var/run/vault-agent-pid"

auto_auth {
    method "approle" {
        mount_path = "auth/approle"
        config {
            role_id_file_path = "/vault/secrets/role_id"
            secret_id_file_path = "/vault/secrets/secret_id"
        }
    }

    sink "file" {
        config {
            path = "/vault/secrets/.env"
        }
    }
}

template {
    source = "/vault/secrets/cloudflare_tunnel_config.ctmpl"
    destination = "/vault/secrets/credentials.json"
    command = "sh -c 'chmod 644 /vault/secrets/credentials.json'"
}
