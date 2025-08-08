
# Vault Agent Configuration for Git Worktree Manager Service
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
    source = "/vault/secrets/git_worktree_manager_config.ctmpl"
    destination = "/vault/secrets/.env"
    command = "sh -c 'chmod 644 /vault/secrets/.env'"
}
