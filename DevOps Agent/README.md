# DevOps Agent - Log Analysis & Incident Resolution

An AI-powered DevOps agent built with **LangGraph + LangChain + OpenAI** that automatically analyzes application logs from **Grafana/Loki**, searches **Runbooks via RAG** for resolution steps, and generates **HTML Incident Reports**.

## Architecture

```
                    ┌─────────────────┐
                    │  Runbooks RAG   │
                    │ (FAISS + OpenAI)│
                    └────────▲────────┘
                             │
┌──────────┐        ┌───────┴────────┐        ┌──────────────┐
│  Grafana │◄──────►│                │──────►  │  HTML Report  │
│  + Loki  │  Logs  │  LangGraph     │         │  (Incident    │
│ (Docker) │        │  Agent         │         │   Summary)    │
└──────────┘        │                │         └──────────────┘
                    └──┬─────────┬───┘
                       │         │
               ┌───────▼──┐  ┌──▼──────┐
               │Docker CLI│  │  SSH    │
               │  Tool    │  │  Tool   │
               └──────────┘  └─────────┘
```

## What It Does

1. **Generates mock logs** simulating a microservices environment (6 services, 4 severity levels)
2. **Pushes logs to Loki** via the HTTP API, viewable in Grafana dashboards
3. **Agent queries Loki** for ERROR and CRITICAL logs
4. **Searches runbooks** using semantic search (FAISS vector store) for matching resolution steps
5. **Runs diagnostics** via Docker CLI and SSH tools
6. **Generates a styled HTML report** with error details, resolutions, and recommendations

## Prerequisites

- **Python 3.10+**
- **Docker Desktop** (running)
- **OpenAI API Key**

## Docker Installation Guide

Docker is required to run the Grafana and Loki infrastructure. Follow the instructions for your operating system below.

### macOS

**Option 1: Docker Desktop (Recommended)**

1. Download Docker Desktop from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Open the `.dmg` file and drag Docker to the Applications folder
3. Launch Docker from Applications
4. Follow the setup wizard and grant the required permissions
5. Verify installation:

```bash
docker --version
docker-compose --version
```

**Option 2: Homebrew**

```bash
brew install --cask docker
open /Applications/Docker.app
```

### Windows

1. **Enable WSL 2** (if not already enabled):

```powershell
wsl --install
```

Restart your computer after this step.

2. Download Docker Desktop from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
3. Run the installer and ensure **"Use WSL 2 instead of Hyper-V"** is checked
4. Restart your computer when prompted
5. Launch Docker Desktop from the Start Menu
6. Verify installation:

```powershell
docker --version
docker-compose --version
```

### Linux (Ubuntu/Debian)

```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group (avoids needing sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Linux (CentOS/RHEL/Fedora)

```bash
# Remove old versions
sudo yum remove docker docker-client docker-client-latest docker-common \
  docker-latest docker-latest-logrotate docker-logrotate docker-engine

# Install prerequisites and add repo
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker Engine and Docker Compose
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### Post-Installation Verification

After installing Docker, confirm everything is working:

```bash
# Check Docker is running
docker info

# Run a test container
docker run hello-world

# Check Docker Compose
docker compose version
```

If `docker compose` is not found, you may have the standalone version — use `docker-compose` (with hyphen) instead.

---

## Setup

### 1. Clone and install dependencies

```bash
cd "DevOps Agent"
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Docker infrastructure

This starts **Grafana** (port 3000) and **Loki** (port 3100):

```bash
docker-compose up -d
```

Verify containers are running:

```bash
docker-compose ps
```

Wait for Loki to be ready:

```bash
curl http://localhost:3100/ready
```

### 4. Generate mock logs

Push 500 sample logs (50 batches of 10) to Loki:

```bash
python log_generator.py
```

You can customize the volume:

```python
from log_generator import run_generator
run_generator(batch_size=20, interval=1.0, total_batches=100)
```

### 5. View logs in Grafana

Open the pre-built dashboard:

```
http://localhost:3000/d/devops-logs-dashboard
```

- **Login**: admin / admin
- Dashboard auto-refreshes every 10 seconds
- Panels: log volume by severity, errors by service, pie chart, log streams

### 6. Run the agent

```bash
python -c "from agent import run_agent; run_agent()"
```

Or with a custom task:

```python
from agent import run_agent

result = run_agent(
    task="Investigate the payment-service for any issues in the last hour."
)
print(f"Report: {result['report_path']}")
```

The HTML report is saved in the `reports/` folder and opens in your browser.

### 7. Use the notebook

For a step-by-step walkthrough, open [devops_agent.ipynb](devops_agent.ipynb) in Jupyter or VS Code.

## Project Structure

```
DevOps Agent/
├── docker-compose.yml              # Grafana + Loki containers
├── loki-config.yml                 # Loki storage and schema config
├── grafana-datasources.yml         # Auto-provision Loki datasource
├── grafana-dashboard-provider.yml  # Dashboard provisioning config
├── grafana-dashboards/
│   └── devops-logs.json            # Pre-built Loki log dashboard
├── log_generator.py                # Mock log generator → Loki
├── runbooks/                       # DevOps runbooks (7 scenarios)
│   ├── database_connection_failure.md
│   ├── out_of_memory.md
│   ├── disk_full.md
│   ├── ssl_tls_failure.md
│   ├── container_crashloop.md
│   ├── service_timeout.md
│   └── payment_gateway_failure.md
├── runbook_rag.py                  # RAG pipeline (FAISS + OpenAI embeddings)
├── tools.py                        # Agent tools (Loki, Docker, SSH, RAG)
├── agent.py                        # LangGraph agent
├── report_generator.py             # HTML incident report generator
├── devops_agent.ipynb              # Interactive notebook
├── requirements.txt                # Python dependencies
└── reports/                        # Generated HTML reports
```

## Agent Tools

| Tool | Description |
|------|-------------|
| `query_loki_logs` | Query Loki with LogQL (any label filter) |
| `query_error_logs` | Shortcut to query ERROR/CRITICAL logs by service |
| `search_runbooks` | Semantic search over runbooks via FAISS |
| `run_docker_command` | Run read-only Docker CLI commands (ps, logs, stats, inspect) |
| `run_ssh_command` | Execute commands on remote hosts (mock mode for demo) |

## Cleanup

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```
