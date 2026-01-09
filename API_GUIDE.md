# NWU Protocol API Guide

## Overview

The NWU Protocol API provides endpoints for managing contributions, verifications, and rewards in the decentralized intelligence verification system.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, authentication is via wallet address parameter. Full Web3 authentication will be added in a future release.

## API Endpoints

### Health & Status

#### GET /

Root endpoint with API information

```json
{
  "status": "healthy",
  "service": "NWU Protocol API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### GET /health

Simple health check

```json
{
  "status": "healthy",
  "service": "nwu-protocol"
}
```

#### GET /api/v1/status

Detailed API status with timestamp

```json
{
  "status": "operational",
  "api_version": "1.0.0",
  "timestamp": "2025-12-30T04:00:00Z"
}
```

### Contributions

#### POST /api/v1/contributions

Create a new contribution

**Query Parameters:**

- `submitter` (required): Ethereum address of the submitter

**Request Body:**

```json
{
  "file_type": "code",
  "metadata": {
    "title": "Smart Contract Optimizer",
    "description": "Gas optimization algorithm",
    "tags": ["solidity", "optimization"],
    "language": "python"
  },
  "content_hash": "abc123def456...",
  "ipfs_hash": "QmT4AeW..."
}
```

**Response (201):**

```json
{
  "id": "contrib_123abc",
  "submitter": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "file_type": "code",
  "metadata": { ... },
  "content_hash": "abc123def456...",
  "ipfs_hash": "QmT4AeW...",
  "status": "pending",
  "quality_score": null,
  "verification_count": 0,
  "reward_amount": null,
  "created_at": "2025-12-30T00:00:00Z",
  "updated_at": "2025-12-30T00:00:00Z"
}
```

#### GET /api/v1/contributions/{contribution_id}

Get contribution details

**Response (200):**

```json
{
  "id": "contrib_123abc",
  "submitter": "0x742d35Cc...",
  "status": "verified",
  "quality_score": 85.5,
  ...
}
```

#### GET /api/v1/contributions/{contribution_id}/status

Get contribution verification status

**Response (200):**

```json
{
  "contribution_id": "contrib_123abc",
  "status": "verified",
  "quality_score": 85.5,
  "verification_count": 3,
  "reward_amount": 100.0,
  "updated_at": "2025-12-30T00:05:00Z"
}
```

#### GET /api/v1/contributions

List contributions with optional filters

**Query Parameters:**

- `submitter` (optional): Filter by submitter address
- `status` (optional): Filter by status (pending, verified, rejected)
- `limit` (optional): Maximum results (default: 100)

**Response (200):**

```json
[
  { "id": "contrib_123abc", ... },
  { "id": "contrib_456def", ... }
]
```

### Verifications

#### POST /api/v1/verifications

Submit a verification for a contribution (typically called by AI agents)

**Request Body:**

```json
{
  "contribution_id": "contrib_123abc",
  "agent_id": "agent-alpha",
  "vote": "approve",
  "score": 85.5,
  "reasoning": "High quality code with good documentation",
  "details": {
    "code_quality": 90,
    "documentation": 85,
    "security": 80,
    "originality": 87
  }
}
```

**Response (201):**

```json
{
  "id": "verif_456def",
  "contribution_id": "contrib_123abc",
  "agent_id": "agent-alpha",
  "vote": "approve",
  "score": 85.5,
  "reasoning": "High quality code...",
  "details": { ... },
  "created_at": "2025-12-30T00:02:00Z"
}
```

#### GET /api/v1/verifications/{verification_id}

Get verification details

#### GET /api/v1/verifications/contribution/{contribution_id}

Get all verifications for a contribution

**Response (200):**

```json
[
  {
    "id": "verif_456def",
    "contribution_id": "contrib_123abc",
    "agent_id": "agent-alpha",
    "vote": "approve",
    "score": 85.5,
    ...
  }
]
```

#### GET /api/v1/verifications/contribution/{contribution_id}/consensus

Get consensus status for a contribution

**Response (200):**

```json
{
  "contribution_id": "contrib_123abc",
  "consensus_reached": true,
  "total_verifications": 3,
  "approval_rate": 1.0,
  "average_score": 85.5,
  "status": "verified"
}
```

## Data Models

### Contribution Status

- `pending`: Waiting for verification
- `verifying`: Being verified by agents
- `verified`: Passed verification
- `rejected`: Failed verification
- `failed`: System error during verification

### Contribution Types

- `code`: Source code
- `dataset`: Data files
- `document`: Documentation/papers
- `other`: Other content types

### Verification Votes

- `approve`: Contribution is valid and high quality
- `reject`: Contribution does not meet standards
- `abstain`: Cannot determine (rare)

### Agent Types

- `agent-alpha`: Quality verification agent
- `agent-beta`: Domain expert (future)
- `agent-gamma`: Security specialist (future)

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Error Responses

All endpoints may return these error responses:

**404 Not Found:**

```json
{
  "error": "Contribution not found",
  "status_code": 404
}
```

**500 Internal Server Error:**

```json
{
  "error": "Failed to create contribution: ...",
  "status_code": 500
}
```

## Examples

### Complete Workflow

1. **Create a contribution:**

```bash
curl -X POST "http://localhost:8000/api/v1/contributions?submitter=0x123..." \
  -H "Content-Type: application/json" \
  -d '{
    "file_type": "code",
    "metadata": {
      "title": "Test",
      "description": "Test contribution",
      "tags": ["test"]
    },
    "content_hash": "abc123"
  }'
```

2. **Submit verification (as agent):**

```bash
curl -X POST "http://localhost:8000/api/v1/verifications" \
  -H "Content-Type: application/json" \
  -d '{
    "contribution_id": "contrib_123abc",
    "agent_id": "agent-alpha",
    "vote": "approve",
    "score": 85.0,
    "reasoning": "Good quality"
  }'
```

3. **Check consensus:**

```bash
curl "http://localhost:8000/api/v1/verifications/contribution/contrib_123abc/consensus"
```

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run API tests only:

```bash
pytest tests/test_api.py -v
```

## Next Steps

- MongoDB integration for persistent storage
- Web3 authentication
- Rate limiting
- WebSocket support for real-time updates
- Reward distribution endpoints
