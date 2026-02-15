# NWU Protocol - System Architecture

## 🌳 Tree Architecture Overview

The NWU Protocol follows a hierarchical tree structure where each component represents a critical part of the ecosystem.

```
                    🌳 NWU PROTOCOL ECOSYSTEM
                              |
              ________________|________________
             |                |                |
        🪵 TRUNK          🧠 NERVOUS       ☁️ ATMOSPHERE
      (Core Backend)      (AI System)    (Infrastructure)
             |                |                |
      ______|______      _____|_____      ____|____
     |      |      |    |     |     |    |    |    |
   Contrib Verif Reward Agent-Alpha Agent-Beta Msg K8s Docker RMQ
   Manager Engine  Calc Alpha Beta  Bus
                              |
                         🌿 BRANCHES
                         (API Layer)
                              |
                      ________|________
                     |        |        |
                   REST    GraphQL   WebSocket
                   API      API      Events
                              |
                         🍃 LEAVES
                      (User Interface)
                              |
                      ________|________
                     |                |
                Contributor        Admin
                  Portal         Dashboard
                              |
                         🌰 ROOTS
                      (Data Layer)
                              |
                      ________|________
                     |        |        |
                  MongoDB    IPFS     Redis
                  (State)   (Files)  (Cache)
                              |
                         🔗 BLOCKCHAIN
                      (Verification Layer)
                              |
                      ________|________
                     |        |        |
                   NWU      Verify    Reward
                  Token     Registry   Distrib
                 (ERC-20)  Contract   Contract
```

## 🏗️ System Components

### 1. Core Backend (The Trunk) 🪵

#### Contribution Manager

- **Purpose**: Handles all contribution ingestion and processing
- **Technology**: Node.js + Express + TypeScript
- **Key Features**:
  - Multi-format file support (code, datasets, documents)
  - IPFS integration for decentralized storage
  - Cryptographic hashing for integrity
  - Version control system
  - File validation (size, type, malware scanning)

#### Verification Engine

- **Purpose**: Orchestrates the AI verification workflow
- **Technology**: Node.js + State Machine pattern
- **Key Features**:
  - Task routing to AI agents via RabbitMQ
  - Consensus calculation (weighted voting)
  - Real-time status tracking
  - WebSocket updates to frontend
  - Retry logic for failed verifications

#### Reward Calculator

- **Purpose**: Computes contributor rewards based on quality
- **Technology**: Node.js + Mathematical algorithms
- **Key Features**:
  - Dynamic reward formula
  - Quality score computation
  - Complexity multipliers
  - Reputation bonuses
  - Token payout queue management

### 2. AI Intelligence (The Nervous System) 🧠

#### Agent-Alpha: Quality Verifier

- **Purpose**: Primary code quality and originality verification
- **Technology**: Python + LangChain + GPT-4
- **Verification Criteria**:
  1. Code Quality (40%)
     - Syntax correctness
     - Best practices adherence
     - Code complexity analysis
  2. Originality (30%)
     - Plagiarism detection
     - Similarity analysis
  3. Security (20%)
     - Vulnerability scanning
     - Dependency analysis
  4. Documentation (10%)
     - Comment quality
     - README completeness

#### Agent-Beta: Domain Expert (Future)

- **Purpose**: Domain-specific verification
- **Specializations**:
  - Machine Learning models
  - Smart contracts
  - Scientific datasets

#### Agent Infrastructure

- RabbitMQ consumer pattern
- OpenAI API integration
- Error handling and logging
- Health monitoring
- Auto-scaling capabilities

### 3. API Layer (The Branches) 🌿

#### REST API

```
POST   /api/v1/contributions          # Upload new contribution
GET    /api/v1/contributions/:id      # Get contribution details
GET    /api/v1/contributions/:id/status # Verification status
GET    /api/v1/users/:address/contributions # User's contributions
GET    /api/v1/users/:address/rewards # Reward balance
POST   /api/v1/auth/connect           # Web3 wallet auth
GET    /api/v1/health                 # System health
```

#### GraphQL API (Future)

- Flexible data querying
- Reduced over-fetching
- Real-time subscriptions

#### WebSocket Events

- Real-time verification updates
- Reward notifications
- System announcements

### 4. User Interface (The Leaves) 🍃

#### Contributor Portal

- **Framework**: Next.js 14 + App Router
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: Zustand + React Query
- **Web3**: Ethers.js v6 + WalletConnect

**Key Pages**:

1. Landing Page
   - Protocol overview
   - How it works
   - Getting started guide

2. Dashboard
   - Contribution history
   - Verification status
   - Reward balance
   - Real-time updates

3. Upload Interface
   - Drag-and-drop file upload
   - Multi-file support
   - Progress indicators
   - Metadata input

4. Profile Page
   - User statistics
   - Reputation score
   - Transaction history
   - Settings

### 5. Infrastructure (The Atmosphere) ☁️

#### Docker Containerization

```yaml
Services:
  - backend-api # Core API server
  - agent-alpha # AI verification agent
  - mongodb # Database
  - redis # Cache
  - rabbitmq # Message bus
  - nginx # Reverse proxy
```

#### Kubernetes Production Setup

```yaml
Components:
  - Deployments # Service replicas
  - Services # Internal networking
  - Ingress # External access
  - ConfigMaps # Configuration
  - Secrets # Sensitive data
  - HPA # Auto-scaling
```

#### RabbitMQ Message Bus

**Queues**:

- `contributions.new` - New contribution submissions
- `verifications.pending` - Verification tasks
- `verifications.complete` - Completed verifications
- `rewards.pending` - Reward calculations
- `rewards.distributed` - Distributed rewards
- `notifications` - User notifications

### 6. Data Persistence (The Roots) 🌰

#### MongoDB Collections

**contributions**

```javascript
{
  _id: ObjectId,
  ipfsHash: String,
  submitter: String (Ethereum address),
  fileType: String,
  metadata: Object,
  verificationStatus: String,
  qualityScore: Number,
  createdAt: Date,
  updatedAt: Date
}
```

**verifications**

```javascript
{
  _id: ObjectId,
  contributionId: ObjectId,
  agentId: String,
  vote: Number (0-100),
  reasoning: String,
  timestamp: Date
}
```

**users**

```javascript
{
  _id: ObjectId,
  address: String (Ethereum address),
  reputationScore: Number,
  totalContributions: Number,
  totalRewards: Number,
  joinedAt: Date
}
```

**rewards**

```javascript
{
  _id: ObjectId,
  userId: ObjectId,
  contributionId: ObjectId,
  amount: Number,
  status: String,
  txHash: String,
  createdAt: Date
}
```

#### IPFS Integration

- **Node**: Self-hosted or Infura
- **Pinning**: Persistent storage
- **Gateway**: Public access via IPFS gateway
- **Content Addressing**: CIDv1 format

#### Redis Cache

- Session storage (30 min TTL)
- API response caching
- Rate limiting counters
- Real-time data (verification progress)

### 7. Blockchain Integration 🔗

#### Smart Contracts (Ethereum)

**NWUToken.sol** (ERC-20)

```solidity
contract NWUToken is ERC20, Ownable {
  uint256 public constant INITIAL_SUPPLY = 1_000_000_000 * 10**18;

  function mint(address to, uint256 amount) external onlyOwner;
  function burn(uint256 amount) external;
}
```

**VerificationRegistry.sol**

```solidity
contract VerificationRegistry {
  struct Verification {
    bytes32 contributionHash;
    uint8 qualityScore;
    uint256 timestamp;
    bool verified;
  }

  mapping(bytes32 => Verification) public verifications;

  function recordVerification(
    bytes32 contributionHash,
    uint8 qualityScore
  ) external onlyVerifier;
}
```

**RewardDistribution.sol**

```solidity
contract RewardDistribution {
  NWUToken public token;

  function distributeReward(
    address contributor,
    uint256 amount
  ) external onlyBackend;

  function claimReward() external;
}
```

## 🔄 Data Flow

### Contribution Workflow

```
1. User uploads file via Portal
   ↓
2. Backend receives file → uploads to IPFS
   ↓
3. Creates MongoDB record with IPFS hash
   ↓
4. Publishes to RabbitMQ queue 'contributions.new'
   ↓
5. Agent-Alpha consumes message
   ↓
6. AI analysis (GPT-4 + custom algorithms)
   ↓
7. Agent submits vote to blockchain
   ↓
8. Backend calculates consensus
   ↓
9. Updates MongoDB with verification result
   ↓
10. Calculates and queues reward
   ↓
11. Distributes tokens via smart contract
   ↓
12. WebSocket notifies user of completion
```

## 🔒 Security Architecture

### Authentication

- Web3 wallet signature verification
- JWT tokens for session management
- Role-based access control (RBAC)

### API Security

- Rate limiting (100 req/min per IP)
- CORS policies
- Input validation and sanitization
- SQL/NoSQL injection prevention
- XSS protection

### Infrastructure Security

- SSL/TLS encryption (Let's Encrypt)
- Kubernetes network policies
- Secret management (Kubernetes Secrets)
- Regular dependency updates
- Automated security scanning

### Smart Contract Security

- OpenZeppelin contracts
- Access control modifiers
- Reentrancy guards
- Professional audit (CertiK/Trail of Bits)

## 📊 Monitoring & Observability

### Metrics (Prometheus)

- API latency (p50, p95, p99)
- Verification throughput
- Agent processing time
- Error rates
- Database performance

### Logging (ELK Stack)

- Application logs
- Access logs
- Error logs
- Audit logs

### Alerting

- Service downtime
- High error rates
- Performance degradation
- Security incidents

### Dashboards (Grafana)

- System health overview
- Real-time metrics
- Historical trends
- Cost analysis

## 🚀 Deployment Strategy

### Development

- Local Docker Compose
- Hot reload enabled
- Mock blockchain (Hardhat)
- Test data seeding

### Staging

- Kubernetes cluster (2 replicas)
- Sepolia testnet
- Full CI/CD pipeline
- Load testing

### Production

- Kubernetes cluster (5+ replicas)
- Ethereum mainnet
- Blue-green deployment
- Automated rollback
- CDN for static assets

## 🔄 CI/CD Pipeline

```
GitHub Push
   ↓
GitHub Actions Triggered
   ↓
Run Tests (Unit + Integration)
   ↓
Build Docker Images
   ↓
Push to Container Registry
   ↓
Deploy to Staging
   ↓
Run E2E Tests
   ↓
Manual Approval Required
   ↓
Deploy to Production
   ↓
Health Check
   ↓
Rollback if Failed
```

## 🎯 Performance Targets

- API Response Time: < 200ms (p95)
- Verification Time: < 5 minutes
- System Uptime: 99.9%
- Concurrent Users: 10,000+
- Daily Verifications: 100,000+

## 📚 Technology Stack Summary

**Backend**: Node.js, Express, TypeScript, MongoDB, Redis, RabbitMQ
**AI Agents**: Python, LangChain, OpenAI GPT-4
**Frontend**: Next.js 14, React, TailwindCSS, Ethers.js
**Blockchain**: Solidity, Hardhat, Ethers.js, OpenZeppelin
**Infrastructure**: Docker, Kubernetes, NGINX, Prometheus, Grafana
**CI/CD**: GitHub Actions, Docker Registry
**Cloud**: AWS/GCP/Azure (flexible)

## 🔮 Future Enhancements

1. **Phase 2**: Multi-chain support (Polygon, BSC)
2. **Phase 3**: Advanced AI agents with specialized domains
3. **Phase 4**: DAO governance for protocol updates
4. **Phase 5**: Mobile applications (iOS/Android)

---

**Version**: 1.0.0  
**Last Updated**: December 26, 2025  
**Status**: Foundation Phase - Active Development
