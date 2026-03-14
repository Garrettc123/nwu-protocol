#!/usr/bin/env python3
"""
CLI tool for managing the Agent Orchestration System.

Usage:
  python agent_cli.py init              - Initialize orchestrator
  python agent_cli.py status            - Show orchestrator status
  python agent_cli.py spawn <type>      - Spawn an agent
  python agent_cli.py list              - List all agents
  python agent_cli.py info <agent_id>   - Show agent info
  python agent_cli.py stop <agent_id>   - Stop an agent
  python agent_cli.py submit <type>     - Submit a task
  python agent_cli.py shutdown          - Shutdown orchestrator
"""

import sys
import asyncio
import aiohttp
import json
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1/agents"


async def call_api(method: str, endpoint: str, data: dict = None) -> dict:
    """Make an API call."""
    url = f"{BASE_URL}{endpoint}"

    try:
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url) as resp:
                    return await resp.json()
            elif method == "POST":
                async with session.post(url, json=data) as resp:
                    return await resp.json()
            elif method == "DELETE":
                async with session.delete(url) as resp:
                    return await resp.json()
            elif method == "PUT":
                async with session.put(url, json=data) as resp:
                    return await resp.json()
    except aiohttp.ClientConnectorError:
        print("❌ Error: Could not connect to backend API")
        print("   Make sure the backend is running at http://localhost:8000")
        sys.exit(1)


async def cmd_init():
    """Initialize the orchestrator."""
    print("Initializing Agent Orchestrator...")
    result = await call_api("POST", "/initialize")

    if result.get('success'):
        print(f"✓ Orchestrator initialized")
        print(f"  Master Agent ID: {result.get('master_agent_id')}")
    else:
        print(f"✗ {result.get('message')}")


async def cmd_status():
    """Show orchestrator status."""
    status = await call_api("GET", "/status")

    print("\n" + "=" * 50)
    print("AGENT ORCHESTRATOR STATUS")
    print("=" * 50)
    print(f"Running:        {status['running']}")
    print(f"Total Agents:   {status['total_agents']}")
    print(f"Auto-scaling:   {status['auto_scaling_enabled']}")
    print(f"Master Agent:   {status['master_agent_id']}")
    print("\nAgents by Type:")
    for agent_type, count in status['agents_by_type'].items():
        if count > 0:
            print(f"  {agent_type:15s}: {count}")
    print("=" * 50 + "\n")


async def cmd_spawn(agent_type: str):
    """Spawn a new agent."""
    print(f"Spawning {agent_type} agent...")

    result = await call_api("POST", "/spawn", {
        "agent_type": agent_type,
        "config": {"name": f"{agent_type.capitalize()}-Agent"}
    })

    if result.get('success'):
        print(f"✓ Agent spawned: {result.get('agent_id')}")
    else:
        print(f"✗ Failed: {result.get('message')}")


async def cmd_list():
    """List all agents."""
    agents = await call_api("GET", "/agents")

    print("\n" + "=" * 80)
    print("ACTIVE AGENTS")
    print("=" * 80)
    print(f"{'Agent ID':<20} {'Type':<15} {'Status':<12} {'Tasks':<8} {'Children':<10}")
    print("-" * 80)

    for agent in agents:
        print(f"{agent['agent_id']:<20} "
              f"{agent['agent_type']:<15} "
              f"{agent['status']:<12} "
              f"{agent['current_tasks']:<8} "
              f"{agent['child_agents']:<10}")

    print("-" * 80)
    print(f"Total: {len(agents)} agents\n")


async def cmd_info(agent_id: str):
    """Show detailed agent information."""
    try:
        agent = await call_api("GET", f"/agents/{agent_id}")

        print("\n" + "=" * 50)
        print(f"AGENT: {agent_id}")
        print("=" * 50)
        print(f"Type:            {agent['agent_type']}")
        print(f"Status:          {agent['status']}")
        print(f"Current Tasks:   {agent['current_tasks']}")
        print(f"Child Agents:    {agent['child_agents']}")
        print(f"Uptime:          {agent['uptime']:.2f}s")
        print("\nMetrics:")
        print(f"  Completed:     {agent['metrics']['tasks_completed']}")
        print(f"  Failed:        {agent['metrics']['tasks_failed']}")
        print(f"  Avg Duration:  {agent['metrics']['average_duration']:.2f}s")
        print(f"  Errors:        {agent['metrics']['error_count']}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"✗ Agent not found: {agent_id}")


async def cmd_stop(agent_id: str):
    """Stop an agent."""
    print(f"Stopping agent {agent_id}...")

    result = await call_api("DELETE", f"/agents/{agent_id}?graceful=true")

    if result.get('success'):
        print(f"✓ Agent stopped: {agent_id}")
    else:
        print(f"✗ Failed: {result.get('message')}")


async def cmd_submit(task_type: str):
    """Submit a task."""
    print(f"Submitting {task_type} task...")

    # Sample task data based on type
    task_data = {}
    if task_type.startswith('verify'):
        task_data = {
            "contribution_id": 999,
            "ipfs_hash": "QmTestHash",
            "file_type": "code"
        }
    elif task_type.startswith('analyze'):
        task_data = {
            "dataset_id": 888,
            "time_range": "30d"
        }

    result = await call_api("POST", "/tasks", {
        "task_type": task_type,
        "task_data": task_data
    })

    if result.get('success'):
        print(f"✓ Task submitted successfully")
    else:
        print(f"✗ Failed: {result.get('message')}")


async def cmd_shutdown():
    """Shutdown the orchestrator."""
    print("Shutting down orchestrator...")
    confirm = input("Are you sure? This will stop all agents. (y/N): ")

    if confirm.lower() == 'y':
        result = await call_api("POST", "/shutdown")
        if result.get('success'):
            print("✓ Orchestrator shutdown complete")
        else:
            print(f"✗ Failed: {result.get('message')}")
    else:
        print("Cancelled")


def print_usage():
    """Print usage information."""
    print("""
Agent Orchestration System CLI

Usage:
  python agent_cli.py <command> [arguments]

Commands:
  init                    Initialize the orchestrator
  status                  Show orchestrator status
  spawn <type>            Spawn an agent (types: master, verifier, analyzer, coordinator, specialist)
  list                    List all active agents
  info <agent_id>         Show detailed agent information
  stop <agent_id>         Stop a specific agent
  submit <task_type>      Submit a task (types: verify_code, verify_dataset, analyze_trends, etc.)
  shutdown                Shutdown the orchestrator (stops all agents)
  help                    Show this help message

Examples:
  python agent_cli.py init
  python agent_cli.py spawn verifier
  python agent_cli.py list
  python agent_cli.py info verifier-abc123
  python agent_cli.py submit verify_code
  python agent_cli.py status

Note: The backend must be running at http://localhost:8000
""")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "init":
            await cmd_init()
        elif command == "status":
            await cmd_status()
        elif command == "spawn":
            if len(sys.argv) < 3:
                print("Error: Agent type required")
                print("Usage: python agent_cli.py spawn <type>")
                sys.exit(1)
            await cmd_spawn(sys.argv[2])
        elif command == "list":
            await cmd_list()
        elif command == "info":
            if len(sys.argv) < 3:
                print("Error: Agent ID required")
                print("Usage: python agent_cli.py info <agent_id>")
                sys.exit(1)
            await cmd_info(sys.argv[2])
        elif command == "stop":
            if len(sys.argv) < 3:
                print("Error: Agent ID required")
                print("Usage: python agent_cli.py stop <agent_id>")
                sys.exit(1)
            await cmd_stop(sys.argv[2])
        elif command == "submit":
            if len(sys.argv) < 3:
                print("Error: Task type required")
                print("Usage: python agent_cli.py submit <task_type>")
                sys.exit(1)
            await cmd_submit(sys.argv[2])
        elif command == "shutdown":
            await cmd_shutdown()
        elif command in ["help", "-h", "--help"]:
            print_usage()
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
