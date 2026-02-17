#!/usr/bin/env python3
"""Test script for Business Cooperation Agent System."""

import asyncio
import json
from datetime import datetime


async def test_agent_factory():
    """Test the agent factory."""
    print("=" * 80)
    print("Testing Agent Factory")
    print("=" * 80)

    try:
        from agent_business_lead.app.agent_factory import AgentFactory, AgentType

        # Create factory
        factory = AgentFactory(max_agents=5)
        print("✓ Agent Factory created")

        # Create different types of agents
        agent_types = [
            AgentType.SALES,
            AgentType.MARKETING,
            AgentType.OPERATIONS,
            AgentType.FINANCE
        ]

        for agent_type in agent_types:
            agent = factory.create_agent(agent_type)
            if agent:
                print(f"✓ Created {agent_type.value} agent: {agent.name}")
            else:
                print(f"✗ Failed to create {agent_type.value} agent")

        # Get factory status
        status = factory.get_factory_status()
        print(f"\n✓ Factory Status:")
        print(f"  Total Agents: {status['total_agents']}")
        print(f"  Available Capacity: {status['available_capacity']}")

        return True

    except Exception as e:
        print(f"✗ Agent Factory test failed: {e}")
        return False


async def test_specialized_agents():
    """Test specialized agent execution."""
    print("\n" + "=" * 80)
    print("Testing Specialized Agents")
    print("=" * 80)

    try:
        from agent_business_lead.app.agent_factory import AgentFactory, AgentType

        factory = AgentFactory()

        # Test Sales Agent
        sales_agent = factory.create_agent(AgentType.SALES, name="Test-Sales-Agent")
        task = {
            "task_id": "test-001",
            "task_type": "lead_generation",
            "data": {"target_market": "technology"}
        }
        result = await sales_agent.execute_task(task)
        print(f"✓ Sales Agent executed task: {result.get('success')}")

        # Test Marketing Agent
        marketing_agent = factory.create_agent(AgentType.MARKETING, name="Test-Marketing-Agent")
        task = {
            "task_id": "test-002",
            "task_type": "content_creation",
            "data": {"content_type": "blog_post"}
        }
        result = await marketing_agent.execute_task(task)
        print(f"✓ Marketing Agent executed task: {result.get('success')}")

        # Test Operations Agent
        ops_agent = factory.create_agent(AgentType.OPERATIONS, name="Test-Ops-Agent")
        task = {
            "task_id": "test-003",
            "task_type": "process_optimization",
            "data": {"process_name": "deployment"}
        }
        result = await ops_agent.execute_task(task)
        print(f"✓ Operations Agent executed task: {result.get('success')}")

        return True

    except Exception as e:
        print(f"✗ Specialized agents test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_task_coordinator():
    """Test task coordinator."""
    print("\n" + "=" * 80)
    print("Testing Task Coordinator")
    print("=" * 80)

    try:
        from agent_business_lead.app.agent_factory import AgentFactory, AgentType
        from agent_business_lead.app.task_coordinator import TaskCoordinator

        factory = AgentFactory()
        coordinator = TaskCoordinator(factory)

        # Create some agents
        factory.create_agent(AgentType.SALES)
        factory.create_agent(AgentType.MARKETING)

        # Submit tasks
        task1 = {
            "task_id": "coord-001",
            "task_type": "lead_generation",
            "data": {}
        }
        task_id1 = await coordinator.submit_task(task1, agent_type=AgentType.SALES)
        print(f"✓ Task {task_id1} submitted")

        task2 = {
            "task_id": "coord-002",
            "task_type": "campaign_management",
            "data": {}
        }
        task_id2 = await coordinator.submit_task(task2, agent_type=AgentType.MARKETING)
        print(f"✓ Task {task_id2} submitted")

        # Get queue status
        status = coordinator.get_queue_status()
        print(f"✓ Queue Status: {status['queued_tasks']} tasks queued")

        return True

    except Exception as e:
        print(f"✗ Task Coordinator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_models():
    """Test database models."""
    print("\n" + "=" * 80)
    print("Testing Database Models")
    print("=" * 80)

    try:
        from backend.app.models import BusinessAgent, BusinessTask

        # Test BusinessAgent model
        print("✓ BusinessAgent model imported successfully")

        # Test BusinessTask model
        print("✓ BusinessTask model imported successfully")

        # Test model attributes
        agent_attrs = ['agent_id', 'agent_type', 'name', 'status', 'capabilities']
        for attr in agent_attrs:
            assert hasattr(BusinessAgent, attr), f"Missing attribute: {attr}"
        print(f"✓ BusinessAgent has all required attributes")

        task_attrs = ['task_id', 'task_type', 'category', 'priority', 'status']
        for attr in task_attrs:
            assert hasattr(BusinessTask, attr), f"Missing attribute: {attr}"
        print(f"✓ BusinessTask has all required attributes")

        return True

    except Exception as e:
        print(f"✗ Database models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("BUSINESS COOPERATION AGENT SYSTEM - TEST SUITE")
    print("=" * 80 + "\n")

    results = []

    # Run tests
    results.append(("Agent Factory", await test_agent_factory()))
    results.append(("Specialized Agents", await test_specialized_agents()))
    results.append(("Task Coordinator", await test_task_coordinator()))
    results.append(("Database Models", await test_database_models()))

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 80 + "\n")

    return passed == total


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/home/runner/work/nwu-protocol/nwu-protocol')
    sys.path.insert(0, '/home/runner/work/nwu-protocol/nwu-protocol/agent-business-lead')

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
