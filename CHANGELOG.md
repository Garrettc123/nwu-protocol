# Changelog

All notable changes to the NWU Protocol will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-11-04

### Finalized

- Promoted from 1.0.0-alpha to **1.0.0 FINAL** after full verification run (2026-11-04): 72/72 tests passing (`pytest tests/`).
- Test dependencies (`pytest`, `pytest-asyncio`) added to `requirements.txt` for reproducible verification.
- Fleet-synced with the Garcar Repo Foundry inventory (313 repos, 2026-11-04).

## [Unreleased]

### Added

- Automated Release Notes (RN) generation system
- CHANGELOG.md file for tracking all changes
- Conventional commit support for automated categorization
- Enhanced release workflow with automatic changelog updates

### Changed

- Release workflow now generates structured release notes automatically

### Deprecated

### Removed

### Fixed

### Security

---

## [1.0.0-alpha] - 2025-12-22

### Added

- Initial Genesis Release of NWU Protocol
- Microservices architecture with 5 distinct layers (The Tree)
- Core Backend (The TRUNK): Contribution Manager, Verification Engine, Reward Calculator
- AI Intelligence (The NERVOUS SYSTEM): Agent-Alpha quality verifier
- API Layer (The BRANCHES): Unified API Gateway
- User Interface (The LEAVES): Next.js 14 Contributor Portal
- Infrastructure (The ATMOSPHERE): Docker & Kubernetes, RabbitMQ
- IPFS integration for decentralized storage
- Event-driven communication via RabbitMQ
- Web3 wallet integration (MetaMask) with Ethers.js v6
- Real-time verification pipeline (<30 seconds)
- Multi-dimensional scoring algorithm
- Consensus mechanism for weighted voting
- Drag-and-drop file upload
- Token reward dashboard
- Comprehensive API documentation
- TypeScript strict mode throughout
- ESLint + Prettier configuration
- Git hooks for code quality

### Infrastructure

- Docker containerized deployment (7 orchestrated services)
- MongoDB for metadata storage
- RabbitMQ for message bus
- Railway deployment platform
- GitHub Actions CI/CD

### Known Limitations

- Testnet only (Sepolia)
- Limited to Agent-Alpha verifier
- Web-only interface (no mobile app)
- Manual token claims
- Max file size: 100MB
- Concurrent uploads limited to 10
- Agent response time: 5-30 seconds

[Unreleased]: https://github.com/Garrettc123/nwu-protocol/compare/v1.0.0-alpha...HEAD
[1.0.0-alpha]: https://github.com/Garrettc123/nwu-protocol/releases/tag/v1.0.0-alpha
