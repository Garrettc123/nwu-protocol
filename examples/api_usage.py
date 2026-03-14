#!/usr/bin/env python3
"""Example script demonstrating NWU Protocol API usage."""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Demonstrate API usage."""
    print_section("NWU Protocol API Usage Example")
    
    # 1. Check API health
    print("1. Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    
    # 2. Create a contribution
    print_section("Creating a Contribution")
    contribution_data = {
        "file_type": "code",
        "metadata": {
            "title": "Smart Contract Gas Optimizer",
            "description": "An algorithm to optimize gas usage in Solidity smart contracts",
            "tags": ["solidity", "optimization", "ethereum", "gas"],
            "language": "python"
        },
        "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "ipfs_hash": "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/contributions",
        params={"submitter": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"},
        json=contribution_data
    )
    
    if response.status_code == 201:
        contribution = response.json()
        contribution_id = contribution["id"]
        print(f"✓ Contribution created successfully!")
        print(f"  ID: {contribution_id}")
        print(f"  Status: {contribution['status']}")
        print(f"  Submitter: {contribution['submitter']}\n")
    else:
        print(f"✗ Failed to create contribution: {response.text}")
        return
    
    # 3. Submit a verification (as AI agent)
    print_section("Submitting AI Agent Verification")
    verification_data = {
        "contribution_id": contribution_id,
        "agent_id": "agent-alpha",
        "vote": "approve",
        "score": 87.5,
        "reasoning": "High quality code with excellent documentation and test coverage. "
                     "Gas optimization algorithm is well-implemented and follows best practices.",
        "details": {
            "code_quality": 90,
            "documentation": 88,
            "security": 85,
            "originality": 87,
            "test_coverage": 85
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/verifications",
        json=verification_data
    )
    
    if response.status_code == 201:
        verification = response.json()
        print(f"✓ Verification submitted successfully!")
        print(f"  Verification ID: {verification['id']}")
        print(f"  Vote: {verification['vote']}")
        print(f"  Score: {verification['score']}/100")
        print(f"  Reasoning: {verification['reasoning'][:80]}...\n")
    else:
        print(f"✗ Failed to submit verification: {response.text}")
        return
    
    # 4. Check consensus
    print_section("Checking Verification Consensus")
    response = requests.get(
        f"{BASE_URL}/api/v1/verifications/contribution/{contribution_id}/consensus"
    )
    
    if response.status_code == 200:
        consensus = response.json()
        print(f"Consensus Status:")
        print(f"  Consensus Reached: {'✓ Yes' if consensus['consensus_reached'] else '✗ No'}")
        print(f"  Total Verifications: {consensus['total_verifications']}")
        print(f"  Approval Rate: {consensus['approval_rate']*100:.1f}%")
        print(f"  Average Score: {consensus['average_score']:.1f}/100")
        print(f"  Status: {consensus['status']}\n")
    
    # 5. Check contribution status
    print_section("Final Contribution Status")
    response = requests.get(
        f"{BASE_URL}/api/v1/contributions/{contribution_id}/status"
    )
    
    if response.status_code == 200:
        status = response.json()
        print(f"Contribution Status:")
        print(f"  ID: {status['contribution_id']}")
        print(f"  Status: {status['status']}")
        print(f"  Quality Score: {status['quality_score']}/100")
        print(f"  Verification Count: {status['verification_count']}")
        if status['reward_amount']:
            print(f"  Reward Amount: {status['reward_amount']} NWU tokens")
        print()
    
    # 6. List all contributions
    print_section("Listing All Contributions")
    response = requests.get(f"{BASE_URL}/api/v1/contributions")
    
    if response.status_code == 200:
        contributions = response.json()
        print(f"Total Contributions: {len(contributions)}")
        for contrib in contributions[:3]:  # Show first 3
            print(f"\n  • {contrib['id']}")
            print(f"    Title: {contrib['metadata']['title']}")
            print(f"    Status: {contrib['status']}")
            if contrib['quality_score']:
                print(f"    Quality: {contrib['quality_score']}/100")
    
    print_section("Example Complete!")
    print("Visit http://localhost:8000/docs for interactive API documentation")
    print()


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server.")
        print("Please ensure the server is running:")
        print("  python3 -m uvicorn app:app --host 0.0.0.0 --port 8000\n")
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
