---
trigger: model_decision
description: use only when you work with virtual machine "Ubuntu" with OrbStack
---

---
description: Rules for interacting with the Ubuntu Linux environment inside OrbStack, executing Linux shell commands, managing Docker sockets, and reading host metrics on macOS.
globs: docker-compose*.yml, **/Dockerfile, services/agent/**/*, **/*.sh
alwaysApply: false
---

# OrbStack & Ubuntu Environment Rules

Activate these rules ONLY when executing commands inside the OrbStack Ubuntu machine, configuring `docker-compose.yml`, working on `services/agent`, or troubleshooting Linux system metrics/networking.

## 1. Environment Topology (macOS Host + OrbStack Ubuntu Target)
- **Developer OS:** macOS (where the IDE and source code live).
- **Target Runtime Environment:** Ubuntu Linux running inside **OrbStack** (acting as a full simulation of our target physical Linux homelab server).
- Never run macOS-specific system commands (`top -l`, `vm_stat`, `diskutil`, `launchctl`) when testing server logic. All host inspection and container commands must target the Linux environment.

## 2. Executing Commands in OrbStack Ubuntu
- To run a shell command directly inside the OrbStack Ubuntu machine from the macOS terminal, prefix it with:
  - Standard user: `orb -m ubuntu <command>` (or `orb <command>` if Ubuntu is set as the default machine).
  - Root privileges: `orb -u root -m ubuntu <command>`.
- When verifying Linux system state (kernel, sensors, mounts, systemd, network interfaces), always execute inside the Ubuntu VM via `orb -m ubuntu ...`.

## 3. Filesystem & Volume Mounting Nuances
- **macOS to Ubuntu Path Mapping:** Files on macOS (`/Users/<user>/...`) are accessible inside OrbStack Ubuntu via `/mnt/mac/Users/<user>/...` (and symlinked to `/Users/<user>/...`).
- **Database & Stateful Volumes:** NEVER bind-mount PostgreSQL data directories (`/var/lib/postgresql/data`) to macOS host folders (`/Users/...`), as macOS filesystem semantics break Postgres permissions and degrade I/O performance. Always use **named Docker volumes** (e.g., `pgdata:/var/lib/postgresql/data`) so data lives natively inside OrbStack's Linux ext4 filesystem.

## 4. Host Metrics & Docker Socket (`services/agent`)
- **Docker Socket Access:** When mounting `/var/run/docker.sock:/var/run/docker.sock` into the `agent` container, ensure the container user has permissions to read/write to the socket (either run `agent` with `group_add: ["${DOCKER_GID:-999}"]` or appropriate permissions).
- **Host Metrics Portability:** The `agent` runs inside a Docker container but must report metrics of the underlying Linux host (OrbStack VM now, physical Linux server later):
  - Mount host paths in `docker-compose.yml`:
    - `/proc:/host/proc:ro`
    - `/sys:/host/sys:ro`
    - `/:/host/root:ro`
  - Configure `agent` via environment variables (`HOST_PROC=/host/proc`, `HOST_ROOT=/host/root`) so `psutil.disk_usage(settings.host_root)` reads the real Linux disk and not the isolated container overlay.
  - Note: Hardware CPU temperature sensors (`/sys/class/thermal`) may return empty lists inside the virtualized OrbStack kernel. Always write defensive fallback logic in `agent` (return `null` / `N/A` instead of crashing if thermal sensors are unavailable in the VM).

## 5. OrbStack Networking Specifics
- Containers in OrbStack are automatically reachable from macOS via `<container_name>.orb.local` or `localhost:<port>`, and the Ubuntu machine is reachable at `ubuntu.orb.local`.
- Inside `docker-compose.yml`, microservices must ALWAYS communicate using internal Docker service names (`http://agent:8001`, `http://core-api:8000`, `postgres:5432`), never `localhost` or `.orb.local`.