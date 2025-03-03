Learn fabric

## Installation

Generate an SSH key pair. (It requires no passphrase)

```powershell
ssh-keygen -t ed25519 -f ".\ssh\id_ed25519" -N '""' -C "Fabric Runner"
```

Build and run containers.

```powershell
docker compose up -d --build --remove-orphans
```

## References
- https://github.com/aoudiamoncef/ubuntu-sshd
