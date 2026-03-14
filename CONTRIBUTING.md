# Contributing to NWU Protocol

## 🎯 Before You Start

Welcome! We're excited to have you contribute. NWU Protocol maintains **world-class engineering standards** to ensure stability, quality, and security.

### Required Reading

Before contributing, please read:

1. **[Governance Framework](GOVERNANCE.md)** - How we make decisions and maintain quality
2. **[Stability Mandate](STABILITY_MANDATE.md)** - Our zero-tolerance commitment to excellence
3. **[Definition of Done](DEFINITION_OF_DONE.md)** - What "done" means for all work
4. **[Coding Standards](CODING_STANDARDS.md)** - How we write code
5. **[Build Standards](BUILD_STANDARDS.md)** - How we build and deploy

### Our Standards

All contributions must meet these non-negotiable requirements:

- ✅ Pass all linting and formatting checks
- ✅ Include tests (80%+ coverage)
- ✅ Pass security scans (no high/critical vulnerabilities)
- ✅ Complete code review by code owner
- ✅ Follow coding standards
- ✅ Include documentation updates
- ✅ Pass all CI/CD checks

See [Definition of Done](DEFINITION_OF_DONE.md) for complete requirements.

---

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

## Code Style & Standards

We follow strict coding standards for all languages. See [Coding Standards](CODING_STANDARDS.md) for complete details.

### Quick Reference

**JavaScript/TypeScript**

- Follow Airbnb JavaScript Style Guide
- Use ESLint + Prettier
- No `any` types
- Explicit return types

**Python**

- Follow PEP 8 and Google Python Style Guide
- Use Black + Flake8 + MyPy
- Type hints required
- Google-style docstrings

**Solidity**

- Follow official Solidity Style Guide
- Use OpenZeppelin standards
- Security-first approach
- Comprehensive testing (95%+ coverage)

**Commit Messages**

- Use Conventional Commits format
- Examples: `feat:`, `fix:`, `docs:`, `refactor:`

## Testing Requirements

All PRs must include:

- ✅ Unit tests with 80%+ coverage (95% for smart contracts)
- ✅ Integration tests for API endpoints
- ✅ Security scanning passes
- ✅ No known bugs
- ✅ Edge cases covered
- ✅ Error paths tested

See [Definition of Done](DEFINITION_OF_DONE.md) for complete testing requirements.

## Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b type/description

# Examples:
# feat/user-authentication
# fix/api-error-handling
# docs/update-readme
# refactor/optimize-queries
```

### 2. Develop Your Changes

- Write code following [Coding Standards](CODING_STANDARDS.md)
- Write tests (TDD preferred)
- Update documentation
- Run linting and tests locally

```bash
# Lint your code
npm run lint        # or: black . && flake8 .

# Run tests
npm test           # or: pytest

# Check coverage
npm test -- --coverage
```

### 3. Commit Your Changes

```bash
git add .
git commit -m "type: description"

# Commit types:
# feat: New feature
# fix: Bug fix
# docs: Documentation
# style: Formatting
# refactor: Code restructuring
# test: Adding tests
# chore: Maintenance
# security: Security fix
```

### 4. Pre-PR Checklist

Before pushing, verify:

- [ ] All tests pass locally
- [ ] Test coverage ≥ 80%
- [ ] Linting passes
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Self-review completed

### 5. Push and Create PR

```bash
git push origin your-branch-name
```

Create a Pull Request on GitHub and:

- Fill out the PR template completely
- Link related issues
- Request review from code owner
- Ensure CI/CD checks pass

### 6. Code Review

- Address all review comments
- Push additional commits as needed
- Discuss constructively if you disagree
- Get approval from code owner

**Code Owner Approval Required**:

- Backend: @Garrettc123
- Frontend: @Garrettc123
- Smart Contracts: @Garrettc123
- Infrastructure: @Garrettc123

### 7. Merge

Once approved and all checks pass:

- Squash and merge (preferred)
- Delete branch after merge
- Monitor deployment

## Quality Gates

Your PR must pass these gates before merge:

### Automated Gates

- ✅ All CI/CD checks pass
- ✅ Linting passes
- ✅ Tests pass
- ✅ Security scan clean
- ✅ Coverage ≥ 80%
- ✅ Build succeeds

### Manual Gates

- ✅ Code owner approval
- ✅ Tiger Team approval (for significant changes)
- ✅ No merge conflicts
- ✅ Documentation updated

## Issue Labels

- `bug` - Bug reports
- `feature` - New feature requests
- `enhancement` - Improvements
- `documentation` - Doc updates
- `good first issue` - Beginner-friendly

## Getting Help

### When You Need Help

1. **Check Documentation** - Start with our comprehensive docs
2. **Search Issues** - Someone may have asked before
3. **Ask the Team** - We're here to help
4. **Tiger Team Office Hours** - Daily support available

### Support Channels

- GitHub Issues for bugs and features
- Team communication channel
- Tiger Team office hours (1 hour daily)
- Technical Leader Q&A (1 hour weekly)

## New to the Project?

If you're new:

1. Read the [Onboarding Guide](ONBOARDING.md)
2. Look for issues labeled `good first issue`
3. Schedule a pairing session with a team member
4. Start with documentation contributions

## Continuous Improvement

We continuously improve our processes:

- Standards are reviewed quarterly
- Feedback is always welcome
- Propose improvements via GitHub issues
- Participate in governance discussions

## Related Documents

- **[Governance Framework](GOVERNANCE.md)** - Decision-making and accountability
- **[Stability Mandate](STABILITY_MANDATE.md)** - Our quality commitment
- **[Definition of Done](DEFINITION_OF_DONE.md)** - Completion criteria
- **[Coding Standards](CODING_STANDARDS.md)** - Code style and quality
- **[Build Standards](BUILD_STANDARDS.md)** - CI/CD and deployment
- **[Metrics Dashboard](METRICS_DASHBOARD.md)** - KPIs and tracking
- **[Onboarding Guide](ONBOARDING.md)** - Getting started
- **[Security Policy](SECURITY.md)** - Security practices

---

**Thank you for contributing to NWU Protocol! Together, we're building something exceptional.** 🚀
