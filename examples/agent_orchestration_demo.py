#!/usr/bin/env python3
"""
Example script demonstrating the multi-agent orchestration system.

This script shows how to:
1. Initialize the orchestrator
2. Spawn different types of agents
3. Submit tasks to agents
4. Monitor agent status
5. Demonstrate hierarchical agent spawning
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


async def call_api(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make an API call."""
    url = f"{BASE_URL}{endpoint}"

    async with aiohttp.ClientSession() as session:
        if method == "GET":
            async with session.get(url) as response:
                return await response.json()
        elif method == "POST":
            async with session.post(url, json=data) as response:
                return await response.json()
        elif method == "DELETE":
            async with session.delete(url) as response:
                return await response.json()
        elif method == "PUT":
            async with session.put(url, json=data) as response:
                return await response.json()


async def initialize_orchestrator():
    """Initialize the agent orchestrator."""
    print("\n" + "=" * 60)
    print("STEP 1: Initializing Agent Orchestrator")
    print("=" * 60)

    result = await call_api("POST", "/api/v1/agents/initialize")
    print(f"✓ Orchestrator initialized")
    print(f"  Master Agent ID: {result.get('master_agent_id')}")

    return result.get('master_agent_id')


async def get_orchestrator_status():
    """Get orchestrator status."""
    print("\n" + "=" * 60)
    print("STEP 2: Checking Orchestrator Status")
    print("=" * 60)

    status = await call_api("GET", "/api/v1/agents/status")
    print(f"✓ Orchestrator Status:")
    print(f"  Running: {status['running']}")
    print(f"  Total Agents: {status['total_agents']}")
    print(f"  Auto-scaling: {status['auto_scaling_enabled']}")
    print(f"  Agents by Type:")
    for agent_type, count in status['agents_by_type'].items():
        print(f"    - {agent_type}: {count}")

    return status


async def spawn_agents(master_agent_id: str):
    """Spawn various types of agents."""
    print("\n" + "=" * 60)
    print("STEP 3: Spawning Additional Agents")
    print("=" * 60)

    spawned_agents = []

    # Spawn 2 verifier agents
    for i in range(2):
        result = await call_api("POST", "/api/v1/agents/spawn", {
            "agent_type": "verifier",
            "parent_agent_id": master_agent_id,
            "config": {
                "name": f"Verifier-{i+1}",
                "max_concurrent_tasks": 5
            }
        })
        if result['success']:
            print(f"✓ Spawned Verifier Agent: {result['agent_id']}")
            spawned_agents.append(result['agent_id'])

    # Spawn 1 analyzer agent
    result = await call_api("POST", "/api/v1/agents/spawn", {
        "agent_type": "analyzer",
        "parent_agent_id": master_agent_id,
        "config": {
            "name": "Analyzer-1",
            "max_concurrent_tasks": 10
        }
    })
    if result['success']:
        print(f"✓ Spawned Analyzer Agent: {result['agent_id']}")
        spawned_agents.append(result['agent_id'])

    # Spawn 1 coordinator agent
    result = await call_api("POST", "/api/v1/agents/spawn", {
        "agent_type": "coordinator",
        "parent_agent_id": master_agent_id,
        "config": {
            "name": "Coordinator-1",
            "can_spawn_agents": True,
            "max_child_agents": 5
        }
    })
    if result['success']:
        print(f"✓ Spawned Coordinator Agent: {result['agent_id']}")
        spawned_agents.append(result['agent_id'])

    return spawned_agents


async def list_all_agents():
    """List all active agents."""
    print("\n" + "=" * 60)
    print("STEP 4: Listing All Active Agents")
    print("=" * 60)

    agents = await call_api("GET", "/api/v1/agents/agents")
    print(f"✓ Found {len(agents)} active agents:")

    for agent in agents:
        print(f"\n  Agent: {agent['agent_id']}")
        print(f"    Type: {agent['agent_type']}")
        print(f"    Status: {agent['status']}")
        print(f"    Tasks Completed: {agent['metrics']['tasks_completed']}")
        print(f"    Current Tasks: {agent['current_tasks']}")
        print(f"    Child Agents: {agent['child_agents']}")
        print(f"    Uptime: {agent['uptime']:.2f}s")

    return agents


async def submit_tasks():
    """Submit various tasks to the orchestrator."""
    print("\n" + "=" * 60)
    print("STEP 5: Submitting Tasks to Agents")
    print("=" * 60)

    # Submit verification tasks
    for i in range(5):
        result = await call_api("POST", "/api/v1/agents/tasks", {
            "task_type": "verify_code",
            "task_data": {
                "contribution_id": 100 + i,
                "ipfs_hash": f"QmTest{i}",
                "file_type": "code"
            },
            "preferred_agent_type": "verifier"
        })
        print(f"✓ Submitted verification task #{i+1}")

    # Submit analysis tasks
    for i in range(3):
        result = await call_api("POST", "/api/v1/agents/tasks", {
            "task_type": "analyze_trends",
            "task_data": {
                "dataset_id": 200 + i,
                "time_range": "30d"
            },
            "preferred_agent_type": "analyzer"
        })
        print(f"✓ Submitted analysis task #{i+1}")

    # Submit coordination task
    result = await call_api("POST", "/api/v1/agents/tasks", {
        "task_type": "coordinate",
        "task_data": {
            "tasks": [
                {"type": "verify_code", "name": "Verify Module A"},
                {"type": "verify_code", "name": "Verify Module B"},
                {"type": "analyze_trends", "name": "Analyze Results"}
            ]
        },
        "preferred_agent_type": "coordinator"
    })
    print(f"✓ Submitted coordination task")


async def monitor_agents(duration: int = 10):
    """Monitor agents for a period of time."""
    print("\n" + "=" * 60)
    print(f"STEP 6: Monitoring Agents ({duration} seconds)")
    print("=" * 60)

    start_time = time.time()
    while time.time() - start_time < duration:
        status = await call_api("GET", "/api/v1/agents/status")
        print(f"\r⟳ Active: {status['total_agents']} | ", end="")

        for agent_type, count in status['agents_by_type'].items():
            if count > 0:
                print(f"{agent_type}: {count} | ", end="")

        await asyncio.sleep(2)

    print("\n✓ Monitoring complete")


async def demonstrate_hierarchical_spawning(coordinator_id: str):
    """Demonstrate hierarchical agent spawning."""
    print("\n" + "=" * 60)
    print("STEP 7: Demonstrating Hierarchical Agent Spawning")
    print("=" * 60)

    # The coordinator will spawn specialist agents
    print(f"  Coordinator {coordinator_id} will spawn specialist agents...")

    # Submit a coordination task that will cause spawning
    result = await call_api("POST", "/api/v1/agents/tasks", {
        "task_type": "coordinate",
        "task_data": {
            "tasks": [
                {
                    "type": "specialized",
                    "name": "Specialized Task 1",
                    "agent_type": "specialist"
                },
                {
                    "type": "specialized",
                    "name": "Specialized Task 2",
                    "agent_type": "specialist"
                }
            ]
        },
        "preferred_agent_type": "coordinator"
    })

    await asyncio.sleep(2)

    # Check coordinator status
    agent_status = await call_api("GET", f"/api/v1/agents/agents/{coordinator_id}")
    print(f"✓ Coordinator now has {agent_status['child_agents']} child agents")


async def test_auto_scaling():
    """Test auto-scaling capabilities."""
    print("\n" + "=" * 60)
    print("STEP 8: Testing Auto-scaling")
    print("=" * 60)

    # Submit many tasks to trigger auto-scaling
    print("  Submitting 20 verification tasks to trigger auto-scaling...")

    for i in range(20):
        await call_api("POST", "/api/v1/agents/tasks", {
            "task_type": "verify_code",
            "task_data": {
                "contribution_id": 1000 + i,
                "ipfs_hash": f"QmScaleTest{i}",
                "file_type": "code"
            },
            "preferred_agent_type": "verifier"
        })

    # Wait for auto-scaling to kick in
    print("  Waiting for auto-scaling (30 seconds)...")
    await asyncio.sleep(30)

    # Check status
    status = await call_api("GET", "/api/v1/agents/status")
    print(f"✓ Auto-scaling complete")
    print(f"  Verifier agents: {status['agents_by_type'].get('verifier', 0)}")


async def configure_orchestrator():
    """Configure orchestrator settings."""
    print("\n" + "=" * 60)
    print("STEP 9: Configuring Orchestrator")
    print("=" * 60)

    # Enable auto-scaling
    result = await call_api("PUT", "/api/v1/agents/config/auto-scaling?enabled=true")
    print(f"✓ Auto-scaling: {result['auto_scaling_enabled']}")

    # Set max agents
    result = await call_api("PUT", "/api/v1/agents/config/max-agents?max_agents_per_type=15")
    print(f"✓ Max agents per type: {result['max_agents_per_type']}")


async def demonstrate_agent_metrics(agent_id: str):
    """Demonstrate agent metrics tracking."""
    print("\n" + "=" * 60)
    print("STEP 10: Agent Metrics")
    print("=" * 60)

    agent_status = await call_api("GET", f"/api/v1/agents/agents/{agent_id}")

    print(f"✓ Metrics for {agent_id}:")
    print(f"  Tasks Completed: {agent_status['metrics']['tasks_completed']}")
    print(f"  Tasks Failed: {agent_status['metrics']['tasks_failed']}")
    print(f"  Average Duration: {agent_status['metrics']['average_duration']:.2f}s")
    print(f"  Error Count: {agent_status['metrics']['error_count']}")


async def cleanup():
    """Cleanup and shutdown."""
    print("\n" + "=" * 60)
    print("STEP 11: Cleanup")
    print("=" * 60)

    # Note: In production, you typically wouldn't shutdown the orchestrator
    # This is just for demonstration purposes

    print("  Orchestrator will continue running...")
    print("  To shutdown, call: POST /api/v1/agents/shutdown")


async def main():
    """Main demonstration function."""
    print("\n" + "═" * 60)
    print("  MULTI-AGENT ORCHESTRATION SYSTEM DEMONSTRATION")
    print("═" * 60)
    print("\nThis demonstration shows the full capabilities of the")
    print("multi-agent orchestration system including:")
    print("  • Dynamic agent spawning")
    print("  • Hierarchical agent structures")
    print("  • Auto-scaling")
    print("  • Task distribution")
    print("  • Health monitoring")
    print("\n")

    try:
        # Initialize orchestrator
        master_agent_id = await initialize_orchestrator()
        await asyncio.sleep(2)

        # Get initial status
        await get_orchestrator_status()
        await asyncio.sleep(1)

        # Spawn additional agents
        spawned_agents = await spawn_agents(master_agent_id)
        await asyncio.sleep(2)

        # List all agents
        agents = await list_all_agents()
        await asyncio.sleep(1)

        # Configure orchestrator
        await configure_orchestrator()
        await asyncio.sleep(1)

        # Submit tasks
        await submit_tasks()
        await asyncio.sleep(2)

        # Monitor agents
        await monitor_agents(duration=10)
        await asyncio.sleep(1)

        # Demonstrate hierarchical spawning
        coordinator_agents = [a for a in agents if a['agent_type'] == 'coordinator']
        if coordinator_agents:
            await demonstrate_hierarchical_spawning(coordinator_agents[0]['agent_id'])
            await asyncio.sleep(2)

        # Show agent metrics
        if spawned_agents:
            await demonstrate_agent_metrics(spawned_agents[0])
            await asyncio.sleep(1)

        # Test auto-scaling (optional - takes longer)
        # await test_auto_scaling()

        # Cleanup
        await cleanup()

        print("\n" + "═" * 60)
        print("  DEMONSTRATION COMPLETE")
        print("═" * 60)
        print("\n✓ All steps completed successfully!")
        print("\nThe agent orchestrator is now running with multiple agents.")
        print("You can continue to submit tasks or monitor agents via the API.")
        print("\nAPI Documentation: http://localhost:8000/docs")
        print("\n")

    except aiohttp.ClientConnectorError:
        print("\n❌ ERROR: Could not connect to the backend API")
        print("   Make sure the backend is running at http://localhost:8000")
        print("   Start it with: python -m backend.app.main")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
