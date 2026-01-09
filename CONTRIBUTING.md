# Contributing to NWU Protocol

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Git

### Local Environment Setup

```bash
# Clone the repository
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol

# Start services with docker-compose
docker-compose up -d

# Install dependencies
npm install
pip install -r requirements.txt

# Run tests
npm test
pytest

# Start development server
npm run dev
```

### Environment Variables

Create `.env.local`:

```
MONGODB_URI=mongodb://localhost:27017/nwu_db
DATABASE_URL=postgresql://user:password@localhost:5432/nwu_db
REDIS_URL=redis://localhost:6379
IPFS_API_URL=http://localhost:5001
OPENAI_API_KEY=sk-...
```

## Code Style

- **JavaScript**: ESLint with Prettier
- **Python**: Black + Flake8
- **Commit Messages**: Conventional Commits

## Testing Requirements

All PRs must include:

- Unit tests with 80%+ coverage
- Integration tests for API endpoints
- Security scanning passes

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -am 'feat: add feature'`
3. Push to your fork and create a Pull Request
4. CI/CD pipeline must pass
5. Code review approval required
6. Merge to main triggers production deployment

## Issue Labels

- `bug` - Bug reports
- `feature` - New feature requests
- `enhancement` - Improvements
- `documentation` - Doc updates
- `good first issue` - Beginner-friendly

## Questions?

Open an issue or reach out on our Discord community.
