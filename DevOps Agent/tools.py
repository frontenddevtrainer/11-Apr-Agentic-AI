"""
Agent Tools - Tools for the DevOps agent to interact with infrastructure.
Includes: Loki log queries, Docker CLI, SSH commands, and Runbook RAG.
"""

import json
import subprocess
import requests
from datetime import datetime, timezone, timedelta
from langchain_core.tools import tool
from runbook_rag import query_runbooks, get_vectorstore

# Cache the vectorstore so it's loaded once
_vectorstore = None


def _get_cached_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = get_vectorstore()
    return _vectorstore


@tool
def query_loki_logs(query: str, hours_back: int = 1, limit: int = 100) -> str:
    """Query logs from Loki/Grafana. Use LogQL query syntax.

    Args:
        query: LogQL query string. Examples:
            - '{job="devops-mock-logs"}' for all logs
            - '{job="devops-mock-logs", level="ERROR"}' for errors only
            - '{job="devops-mock-logs", service="api-gateway"}' for a specific service
        hours_back: How many hours back to search (default: 1)
        limit: Maximum number of log entries to return (default: 100)
    """
    loki_url = "http://localhost:3100/loki/api/v1/query_range"

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours_back)

    params = {
        "query": query,
        "start": int(start_time.timestamp() * 1e9),
        "end": int(end_time.timestamp() * 1e9),
        "limit": limit,
        "direction": "backward",
    }

    try:
        resp = requests.get(loki_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        if data.get("data", {}).get("result"):
            for stream in data["data"]["result"]:
                labels = stream.get("stream", {})
                service = labels.get("service", "unknown")
                level = labels.get("level", "unknown")
                for ts, line in stream.get("values", []):
                    try:
                        parsed = json.loads(line)
                        msg = parsed.get("message", line)
                    except json.JSONDecodeError:
                        msg = line
                    results.append(f"[{level}] [{service}] {msg}")

        if not results:
            return "No logs found matching the query."

        return f"Found {len(results)} log entries:\n\n" + "\n".join(results[:limit])

    except requests.exceptions.RequestException as e:
        return f"Error querying Loki: {e}"


@tool
def query_error_logs(service: str = "", hours_back: int = 1) -> str:
    """Query ERROR and CRITICAL logs from Loki, optionally filtered by service.

    Args:
        service: Service name to filter (e.g., 'api-gateway'). Leave empty for all services.
        hours_back: How many hours back to search (default: 1)
    """
    if service:
        query = f'{{job="devops-mock-logs", level=~"ERROR|CRITICAL", service="{service}"}}'
    else:
        query = '{job="devops-mock-logs", level=~"ERROR|CRITICAL"}'

    return query_loki_logs.invoke({"query": query, "hours_back": hours_back, "limit": 200})


@tool
def run_docker_command(command: str) -> str:
    """Run a Docker CLI command to inspect containers, images, or resources.

    Only allows read-only/safe Docker commands (ps, logs, stats, inspect, images).

    Args:
        command: Docker command to run (e.g., 'ps', 'logs <container>', 'stats --no-stream')
    """
    allowed_prefixes = ["ps", "logs", "stats", "inspect", "images", "network ls", "volume ls", "system df"]

    is_allowed = any(command.strip().startswith(prefix) for prefix in allowed_prefixes)
    if not is_allowed:
        return f"Command not allowed for safety. Allowed commands: {', '.join(allowed_prefixes)}"

    try:
        result = subprocess.run(
            f"docker {command}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout or result.stderr
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
        return output if output.strip() else "Command completed with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running Docker command: {e}"


@tool
def run_ssh_command(host: str, command: str) -> str:
    """Run a command on a remote server via SSH (mock - simulates SSH for demo).

    Args:
        host: Hostname or IP to connect to
        command: Command to execute on remote host
    """
    # Mock SSH for demonstration - simulates common diagnostic commands
    mock_responses = {
        "df -h": """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   78G   22G  78% /
/dev/sdb1       500G  420G   80G  84% /data
tmpfs           16G   2.1G   14G  13% /tmp""",
        "free -h": """              total        used        free      shared  buff/cache   available
Mem:           32Gi       24Gi       2.1Gi       512Mi       5.8Gi       7.2Gi
Swap:          8.0Gi      1.2Gi      6.8Gi""",
        "uptime": " 14:32:01 up 45 days, 3:21,  2 users,  load average: 2.45, 1.89, 1.62",
        "top -bn1 | head -5": """top - 14:32:01 up 45 days,  3:21,  2 users,  load average: 2.45, 1.89, 1.62
Tasks: 234 total,   3 running, 229 sleeping,   0 stopped,   2 zombie
%Cpu(s): 45.2 us,  8.3 sy,  0.0 ni, 42.1 id,  3.2 wa,  0.0 hi,  1.2 si,  0.0 st
MiB Mem:  32168.0 total,  2156.3 free, 24892.1 used,  5119.6 buff/cache
MiB Swap:  8192.0 total,  6963.2 free,  1228.8 used.  7372.8 avail Mem""",
    }

    for key, response in mock_responses.items():
        if key in command:
            return f"[SSH {host}] $ {command}\n{response}"

    return f"[SSH {host}] $ {command}\nCommand executed successfully (mock mode)."


@tool
def search_runbooks(query: str) -> str:
    """Search the runbook knowledge base for resolution steps matching an error or issue.

    Args:
        query: Description of the error or issue to search for (e.g., 'database connection refused',
               'out of memory OOM killed', 'disk full no space left')
    """
    vectorstore = _get_cached_vectorstore()
    return query_runbooks(query, vectorstore)


ALL_TOOLS = [query_loki_logs, query_error_logs, run_docker_command, run_ssh_command, search_runbooks]
