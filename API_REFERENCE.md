# NWU Protocol API Reference

Complete API documentation for the NWU Protocol Backend.

## Base URL

```
Development: http://localhost:8000
Production: https://api.nwu-protocol.com
```

## Authentication

The NWU Protocol uses Web3 wallet signature verification with JWT tokens.

### Authentication Flow

1. **Connect Wallet** - Get a nonce to sign
2. **Verify Signature** - Sign the nonce and get a JWT token
3. **Use Token** - Include token in subsequent requests

### Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

---

## Endpoints

### Authentication

#### POST /api/v1/auth/connect

Initiate wallet connection and get a nonce to sign.

**Request:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
}
```

**Response:**

```json
{
  "nonce": "random_nonce_string",
  "message": "Sign this message to authenticate with NWU Protocol...",
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
}
```

#### POST /api/v1/auth/verify

Verify wallet signature and receive JWT token.

**Request:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "signature": "0x1234...",
  "nonce": "random_nonce_string"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "expires_in": 86400
}
```

#### POST /api/v1/auth/logout

Logout and invalidate session.

**Query Parameters:**

- `address` (required): Ethereum address

**Response:**

```json
{
  "message": "Logged out successfully"
}
```

#### GET /api/v1/auth/status

Check authentication status.

**Query Parameters:**

- `address` (required): Ethereum address

**Response:**

```json
{
  "authenticated": true,
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb"
}
```

---

### Contributions

#### POST /api/v1/contributions/

Upload a new contribution.

**Form Data:**

- `file` (required): File to upload
- `title` (required): Title of the contribution
- `description` (optional): Description
- `file_type` (required): Type of file (code, dataset, document)
- `user_address` (required): Ethereum address
- `metadata` (optional): JSON string with additional metadata

**Response:**

```json
{
  "id": 1,
  "user_id": 1,
  "ipfs_hash": "QmTzQ1JRkWErjk39mryYw2WVaphAZNAREyMchXzYyzn",
  "file_name": "example.py",
  "file_type": "code",
  "file_size": 1024,
  "title": "Machine Learning Model",
  "description": "A neural network implementation",
  "status": "verifying",
  "quality_score": null,
  "verification_count": 0,
  "created_at": "2024-01-10T10:00:00",
  "updated_at": "2024-01-10T10:00:00"
}
```

#### GET /api/v1/contributions/{id}

Get contribution details by ID.

**Response:**

```json
{
  "id": 1,
  "user_id": 1,
  "ipfs_hash": "QmTzQ1JRkWErjk39mryYw2WVaphAZNAREyMchXzYyzn",
  "file_name": "example.py",
  "file_type": "code",
  "file_size": 1024,
  "title": "Machine Learning Model",
  "description": "A neural network implementation",
  "status": "verified",
  "quality_score": 85.5,
  "verification_count": 3,
  "created_at": "2024-01-10T10:00:00",
  "updated_at": "2024-01-10T10:30:00"
}
```

#### GET /api/v1/contributions/{id}/status

Get real-time verification status.

**Response:**

```json
{
  "contribution_id": 1,
  "status": "verifying",
  "quality_score": null,
  "verification_count": 1,
  "updated_at": "2024-01-10T10:15:00"
}
```

#### GET /api/v1/contributions/

List all contributions with optional filters.

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 50, max: 100)
- `status` (optional): Filter by status (pending, verifying, verified, rejected)
- `user_address` (optional): Filter by user address

**Response:**

```json
[
  {
    "id": 1,
    "title": "Machine Learning Model",
    "status": "verified",
    "quality_score": 85.5,
    ...
  },
  ...
]
```

#### GET /api/v1/contributions/{id}/file

Download the original file from IPFS.

**Response:** Binary file download

---

### Users

#### POST /api/v1/users/

Create a new user.

**Request:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "username": "alice",
  "email": "alice@example.com"
}
```

**Response:**

```json
{
  "id": 1,
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "username": "alice",
  "email": "alice@example.com",
  "reputation_score": 0.0,
  "total_contributions": 0,
  "total_rewards": 0.0,
  "is_active": true,
  "created_at": "2024-01-10T10:00:00"
}
```

#### GET /api/v1/users/{address}

Get user by Ethereum address.

**Response:**

```json
{
  "id": 1,
  "address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "username": "alice",
  "reputation_score": 75.5,
  "total_contributions": 10,
  "total_rewards": 1250.5,
  "created_at": "2024-01-10T10:00:00"
}
```

#### GET /api/v1/users/{address}/contributions

Get all contributions by a user.

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 50)

**Response:**

```json
{
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "total_contributions": 10,
  "contributions": [
    {
      "id": 1,
      "title": "Machine Learning Model",
      ...
    }
  ]
}
```

#### GET /api/v1/users/{address}/rewards

Get reward history for a user.

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 50)

**Response:**

```json
{
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "total_rewards": 1250.5,
  "pending_amount": 200.0,
  "distributed_amount": 1050.5,
  "rewards": [
    {
      "id": 1,
      "contribution_id": 1,
      "amount": 125.5,
      "status": "distributed",
      "tx_hash": "0xabcdef...",
      "created_at": "2024-01-10T10:00:00",
      "distributed_at": "2024-01-10T11:00:00"
    }
  ]
}
```

#### GET /api/v1/users/{address}/stats

Get user statistics.

**Response:**

```json
{
  "user_address": "0x742d35cc6634c0532925a3b844bc9e7595f0beb",
  "reputation_score": 75.5,
  "total_contributions": 10,
  "verified_contributions": 8,
  "average_quality_score": 82.3,
  "total_rewards": 1250.5,
  "joined_at": "2024-01-10T10:00:00"
}
```

---

### Verifications

#### POST /api/v1/verifications/

Submit a verification result (agents only).

**Request:**

```json
{
  "contribution_id": 1,
  "agent_id": "agent-alpha-001",
  "agent_type": "alpha",
  "vote_score": 85.5,
  "quality_score": 82.0,
  "originality_score": 88.0,
  "security_score": 86.0,
  "documentation_score": 84.0,
  "reasoning": "High-quality code with good documentation...",
  "details": {
    "file_type": "code",
    "language": "python",
    "lines_of_code": 250
  }
}
```

**Response:**

```json
{
  "id": 1,
  "contribution_id": 1,
  "agent_id": "agent-alpha-001",
  "agent_type": "alpha",
  "vote_score": 85.5,
  "status": "completed",
  "created_at": "2024-01-10T10:15:00"
}
```

#### GET /api/v1/verifications/contribution/{contribution_id}

Get all verifications for a contribution.

**Response:**

```json
[
  {
    "id": 1,
    "contribution_id": 1,
    "agent_id": "agent-alpha-001",
    "agent_type": "alpha",
    "vote_score": 85.5,
    "quality_score": 82.0,
    ...
  }
]
```

---

### System

#### GET /health

System health check.

**Response:**

```json
{
  "status": "healthy",
  "service": "nwu-protocol-backend",
  "version": "1.0.0",
  "timestamp": "2024-01-10T10:00:00",
  "checks": {
    "database": true,
    "ipfs": true,
    "rabbitmq": true,
    "redis": true
  }
}
```

#### GET /

API information.

**Response:**

```json
{
  "name": "NWU Protocol API",
  "description": "Decentralized Intelligence & Verified Truth Protocol",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### GET /api/v1/info

Detailed API information.

**Response:**

```json
{
  "name": "NWU Protocol API",
  "description": "Decentralized Intelligence & Verified Truth Protocol",
  "version": "1.0.0",
  "endpoints": {
    "contributions": "/api/v1/contributions",
    "users": "/api/v1/users",
    "verifications": "/api/v1/verifications",
    "health": "/health",
    "docs": "/docs"
  }
}
```

---

## WebSocket

### /ws/contributions/{contribution_id}

Real-time updates for contribution verification status.

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/contributions/1');

ws.onmessage = event => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};

// Keep-alive ping
setInterval(() => ws.send('ping'), 30000);
```

**Message Types:**

Initial status:

```json
{
  "type": "status",
  "contribution_id": 1,
  "status": "verifying",
  "quality_score": null,
  "verification_count": 0,
  "updated_at": "2024-01-10T10:00:00"
}
```

Update notification:

```json
{
  "type": "update",
  "contribution_id": 1,
  "status": "verified",
  "quality_score": 85.5,
  "timestamp": 1234567890
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
  "error": "Invalid request parameters",
  "status_code": 400
}
```

### 401 Unauthorized

```json
{
  "error": "Authentication required",
  "status_code": 401
}
```

### 404 Not Found

```json
{
  "error": "Resource not found",
  "status_code": 404
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "status_code": 500
}
```

---

## Rate Limiting

- **Default:** 100 requests per minute per IP
- **Authenticated:** 1000 requests per minute per user
- Headers:
  - `X-RateLimit-Limit`: Maximum requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

## Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Code Examples

### Python

```python
import requests

# Connect wallet
response = requests.post('http://localhost:8000/api/v1/auth/connect', json={
    'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb'
})
nonce_data = response.json()

# Sign message with your wallet
# signature = sign_message(nonce_data['message'])

# Verify and get token
response = requests.post('http://localhost:8000/api/v1/auth/verify', json={
    'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
    'signature': signature,
    'nonce': nonce_data['nonce']
})
token = response.json()['access_token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8000/api/v1/users/0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', headers=headers)
```

### JavaScript

```javascript
const axios = require('axios');

async function authenticate(address, signature, nonce) {
  const response = await axios.post('http://localhost:8000/api/v1/auth/verify', {
    address,
    signature,
    nonce,
  });

  return response.data.access_token;
}

async function uploadContribution(token, file, metadata) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title);
  formData.append('file_type', metadata.file_type);
  formData.append('user_address', metadata.user_address);

  const response = await axios.post('http://localhost:8000/api/v1/contributions/', formData, {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}
```

---

## Support

For API issues:

- GitHub Issues: https://github.com/Garrettc123/nwu-protocol/issues
- Email: support@nwu-protocol.com
