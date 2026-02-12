# NWU Protocol Onboarding Guide

## Welcome to NWU Protocol! 🎉

This guide will help you get started with the project and understand our commitment to excellence, quality, and stability.

---

## Overview

NWU Protocol is a decentralized intelligence and verified truth platform that combines AI-powered verification with blockchain immutability. We maintain **world-class engineering standards** to ensure reliability, security, and quality.

---

## Core Values & Standards

### Our Commitment to Excellence

1. **Quality First** - We never compromise on code quality or security
2. **Stability Mandate** - Zero-tolerance for technical debt and poor practices
3. **Continuous Improvement** - We're always learning and evolving
4. **Transparency** - All decisions and metrics are visible to the team
5. **Accountability** - Clear ownership and responsibility

### Required Reading (Week 1)

Please read these documents in order:

1. ✅ [README.md](README.md) - Project overview
2. ✅ [GOVERNANCE.md](GOVERNANCE.md) - How we make decisions
3. ✅ [STABILITY_MANDATE.md](STABILITY_MANDATE.md) - Our quality commitment
4. ✅ [DEFINITION_OF_DONE.md](DEFINITION_OF_DONE.md) - What "done" means
5. ✅ [CODING_STANDARDS.md](CODING_STANDARDS.md) - How we write code
6. ✅ [BUILD_STANDARDS.md](BUILD_STANDARDS.md) - How we build and deploy
7. ✅ [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
8. ✅ [SECURITY.md](SECURITY.md) - Security policies

---

## Getting Started

### Week 1: Environment Setup

#### Day 1: System Setup

**Prerequisites**

```bash
# Check your system
node --version  # Should be >= 18.0.0
npm --version   # Should be >= 9.0.0
python --version  # Should be >= 3.11
docker --version
docker-compose --version
git --version
```

**Clone Repository**

```bash
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
```

**Environment Configuration**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
# Ask team lead for development API keys
nano .env
```

**First Build**

```bash
# Install dependencies
npm install

# Start infrastructure services
docker-compose up -d

# Verify services are running
make status

# Run health checks
make health
```

**Verify Your Setup**

```bash
# Should see all services running
make validate

# Should pass
npm test

# Access the API docs
open http://localhost:8000/docs
```

#### Day 2-3: Codebase Exploration

**Understand the Architecture**

```bash
# Read architecture documentation
cat ARCHITECTURE.md

# Explore the codebase structure
tree -L 2 -I 'node_modules|dist|build'
```

**Key Directories**:

- `backend/` - FastAPI backend service
- `frontend/` - Next.js frontend application
- `contracts/` - Solidity smart contracts
- `agent-alpha/` - AI verification agent
- `.github/` - CI/CD workflows and templates
- `scripts/` - Utility scripts

**Run the Application**

```bash
# Terminal 1: Backend and services
./deploy.sh

# Terminal 2: Frontend (optional)
cd frontend
npm install
npm run dev
```

#### Day 4-5: Make Your First Contribution

**Find a Good First Issue**

```bash
# Look for issues labeled "good first issue"
# https://github.com/Garrettc123/nwu-protocol/labels/good%20first%20issue
```

**Create a Branch**

```bash
git checkout -b feature/my-first-contribution
```

**Make Changes**

```bash
# Edit files
# Write tests
# Update documentation
```

**Follow the Standards**

```bash
# Run linting
npm run lint

# Run tests
npm test

# Check coverage
npm test -- --coverage
```

**Submit PR**

```bash
git add .
git commit -m "feat: add feature xyz"
git push origin feature/my-first-contribution

# Create PR on GitHub
# Fill out the PR template completely
```

### Week 2: Deep Dive

#### Day 6-7: Component Deep Dive

Pick one component to focus on:

**Backend (FastAPI)**

```bash
cd backend
cat README.md
pip install -r requirements.txt
pytest
```

**Frontend (Next.js)**

```bash
cd frontend
cat README.md
npm install
npm run dev
```

**Smart Contracts (Solidity)**

```bash
cd contracts
cat README.md
npm install
npx hardhat test
```

**AI Agent (Python)**

```bash
cd agent-alpha
cat README.md
pip install -r requirements.txt
python -m app.main
```

#### Day 8-9: CI/CD Understanding

**Study Workflows**

```bash
# Review CI/CD workflows
cat .github/workflows/ci-cd.yml
cat .github/workflows/quality-checks.yml
cat .github/workflows/defender-for-devops.yml
```

**Watch a Pipeline Run**

1. Make a change
2. Push to your branch
3. Watch GitHub Actions run
4. Understand each step
5. Fix any failures

#### Day 10: Security Training

**Complete Security Training**

- OWASP Top 10
- Secure coding practices
- Input validation
- Authentication/Authorization
- Secrets management

**Security Checklist**

- [ ] Never commit secrets
- [ ] Always validate inputs
- [ ] Use parameterized queries
- [ ] Implement proper error handling
- [ ] Follow principle of least privilege

### Week 3: Team Integration

#### Week 3: Participate in Team Processes

**Daily Standups**

- Join daily team sync (15 minutes)
- Share what you're working on
- Ask questions
- Listen to others

**Code Reviews**

- Start reviewing others' PRs
- Provide constructive feedback
- Learn from code review comments
- Use the code review checklist

**Tiger Team Meetings**

- Observe weekly decision meetings
- Understand governance in action
- See how decisions are made

**Pair Programming**

- Schedule sessions with team members
- Learn their workflows
- Share your knowledge
- Build relationships

---

## Development Workflow

### Standard Workflow

1. **Select Task**
   - Choose from backlog
   - Understand requirements
   - Clarify with team if needed

2. **Create Branch**

   ```bash
   git checkout -b type/description
   # Examples:
   # feat/user-authentication
   # fix/api-error-handling
   # docs/update-readme
   ```

3. **Develop**
   - Write code following standards
   - Write tests (TDD preferred)
   - Update documentation
   - Run linting and tests locally

4. **Commit**

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
   ```

5. **Push & PR**

   ```bash
   git push origin your-branch-name
   ```

   - Create PR on GitHub
   - Fill out PR template completely
   - Link related issues
   - Request review from code owner

6. **Review & Iterate**
   - Address review comments
   - Push additional commits
   - Discuss if you disagree
   - Get approval

7. **Merge**
   - Squash and merge (preferred)
   - Delete branch after merge

### Quality Checklist

Before submitting a PR, ensure:

- [ ] All tests pass locally
- [ ] Test coverage ≥ 80%
- [ ] Linting passes
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] PR template completed
- [ ] Self-review completed

---

## Tools & Resources

### Required Tools

**Development**

- **IDE**: VS Code (recommended) with extensions
  - ESLint
  - Prettier
  - Python
  - Solidity
  - Docker
  - GitLens

**Terminal**

- **Shell**: Bash/Zsh
- **Git**: Latest version
- **Docker**: For local services
- **Make**: For convenience commands

**Browsers**

- Chrome/Firefox with DevTools
- React DevTools extension

### Optional Tools

- **Postman/Insomnia**: API testing
- **TablePlus/DBeaver**: Database management
- **Hardhat**: Smart contract development
- **GitHub CLI**: `gh` command

### Learning Resources

**Documentation**

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Solidity Docs](https://docs.soliditylang.org/)
- [Docker Docs](https://docs.docker.com/)

**Internal Resources**

- Project documentation in `/docs`
- API documentation at `/docs` endpoint
- Architecture diagrams in `ARCHITECTURE.md`
- Team wiki (if available)

---

## Getting Help

### When You're Stuck

1. **Check Documentation** - Most answers are documented
2. **Search Issues** - Someone may have asked before
3. **Ask in Slack/Discord** - Team is here to help
4. **Schedule Pairing** - Learn together
5. **Create Issue** - Document new problems

### Support Channels

**Daily Support**

- Tiger Team office hours (1 hour daily)
- Team Slack/Discord channel
- Pair programming sessions

**Weekly Support**

- Technical Leader Q&A (1 hour weekly)
- Team all-hands meeting

**Resources**

- [Contributing Guide](CONTRIBUTING.md)
- [FAQ](FAQ.md) (if exists)
- Team wiki

---

## Common Tasks

### Running Tests

```bash
# All tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific file
npm test path/to/test.js
```

### Linting & Formatting

```bash
# Lint
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format
```

### Database Operations

```bash
# Run migrations
make migrate

# Reset database
make db-reset

# Seed test data
make db-seed
```

### Docker Operations

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service]

# Stop services
docker-compose down

# Rebuild
docker-compose up -d --build
```

---

## Performance Expectations

### First 30 Days

**Week 1**

- Environment setup complete
- First PR merged
- All required reading done
- Team introductions complete

**Week 2**

- Component deep dive complete
- 3-5 PRs merged
- Participating in code reviews
- Understanding CI/CD

**Week 3-4**

- Independently picking up tasks
- Providing meaningful code reviews
- Contributing to discussions
- Following all standards

### First 90 Days

- Fully productive team member
- Mentoring newer team members
- Contributing to standards discussions
- Taking ownership of features

---

## Success Criteria

You're successfully onboarded when you can:

- [ ] Set up the development environment independently
- [ ] Navigate the codebase confidently
- [ ] Follow all coding standards
- [ ] Write tests that meet coverage requirements
- [ ] Submit PRs that pass all checks
- [ ] Provide valuable code reviews
- [ ] Contribute to team discussions
- [ ] Help onboard new team members

---

## Continuous Learning

### Monthly Goals

- Learn one new tool or technology
- Read one technical article/book
- Complete one online course
- Contribute to documentation
- Mentor someone

### Quarterly Goals

- Master one component of the system
- Lead a feature from start to finish
- Present at team meeting
- Contribute to standards evolution
- Achieve high quality metrics

---

## Feedback & Improvement

### Weekly Check-ins

- Progress review
- Blocker identification
- Learning needs
- Feedback session

### Monthly 1-on-1s

- Career development
- Performance review
- Goal setting
- Skill development

---

## Related Documents

- [Governance Framework](GOVERNANCE.md)
- [Stability Mandate](STABILITY_MANDATE.md)
- [Definition of Done](DEFINITION_OF_DONE.md)
- [Coding Standards](CODING_STANDARDS.md)
- [Contributing Guide](CONTRIBUTING.md)

---

## Questions?

Don't hesitate to ask! We're here to help you succeed.

**Welcome to the team! Let's build something amazing together! 🚀**

---

**Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Tiger Team  
**Review Cycle**: Quarterly
