# Contributing to NWU Protocol

First off, thank you for considering contributing to the NWU Protocol! It's people like you that will help build the future of decentralized intelligence and verified truth.

## 🌍 Vision

The NWU Protocol is building the cognitive infrastructure for humanity's next epoch. Every contribution, no matter how small, helps us move closer to a world where truth is decentralized, verified, and rewarded.

## 📄 Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [garrett@nwu-protocol.com](mailto:garrett@nwu-protocol.com).

## 🚀 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** to demonstrate the steps
- **Describe the behavior you observed** and explain what you expected
- **Include screenshots** if relevant
- **Note your environment** (OS, Node version, Docker version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the proposed enhancement
- **Explain why this enhancement would be useful** to most users
- **List any alternative solutions** you've considered

### Pull Requests

The process described here has several goals:

- Maintain code quality
- Fix problems that are important to users
- Engage the community in building the best possible protocol
- Enable a sustainable system for maintainers to review contributions

#### Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Follow the naming convention**: `feature/your-feature` or `fix/your-bugfix`
3. **Make your changes** and ensure they follow our coding standards
4. **Write or update tests** as needed
5. **Ensure all tests pass** (`npm test` for Node.js, `pytest` for Python)
6. **Update documentation** if you're changing functionality
7. **Commit your changes** using [Conventional Commits](https://www.conventionalcommits.org/)
8. **Push to your fork** and submit a pull request

#### Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

**Examples:**
```
feat(api): add contribution upload endpoint

fix(agent): resolve plagiarism detection timeout

docs(readme): update installation instructions
```

## 🛠️ Development Setup

### Prerequisites

- Node.js v18+
- Python 3.10+
- Docker & Docker Compose
- Git

### Local Development

1. **Clone your fork**
```bash
git clone https://github.com/YOUR_USERNAME/nwu-protocol.git
cd nwu-protocol
```

2. **Install dependencies**
```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
cd agents
pip install -r requirements.txt
cd ..
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start development environment**
```bash
docker-compose up
```

5. **Run tests**
```bash
# Node.js tests
npm test

# Python tests
cd agents
pytest
```

## 📝 Coding Standards

### TypeScript/JavaScript

- Use **TypeScript** with strict mode enabled
- Follow **ESLint** configuration
- Use **Prettier** for code formatting
- Write **JSDoc comments** for public APIs
- Maintain **80%+ test coverage**

### Python

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Write **docstrings** for all public functions/classes
- Use **Black** for code formatting
- Write **unit tests** using pytest

### File Organization

```
nwu-protocol/
├── services/          # Microservices (Node.js)
│   ├── api/
│   ├── verification/
│   └── rewards/
├── agents/           # AI Agents (Python)
│   └── agent-alpha/
├── frontend/         # Next.js application
├── contracts/        # Solidity smart contracts
├── docs/             # Documentation
└── docker/           # Docker configurations
```

## 🧪 Testing

### Unit Tests

- Write tests for all new features
- Ensure existing tests pass before submitting PR
- Aim for 80%+ code coverage
- Use descriptive test names

### Integration Tests

- Test interactions between services
- Verify message queue flows
- Test database operations
- Validate API contracts

### Running Tests

```bash
# All tests
npm run test:all

# Unit tests only
npm test

# Integration tests
npm run test:integration

# Coverage report
npm run test:coverage
```

## 🔍 Code Review Process

All submissions require review. We use GitHub pull requests for this purpose:

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by at least one maintainer
3. **Testing** in staging environment
4. **Approval** from project maintainer
5. **Merge** to main branch

### What We Look For

- **Code quality**: Clean, readable, maintainable
- **Test coverage**: Adequate tests for new code
- **Documentation**: Updated docs for new features
- **Performance**: No significant performance regressions
- **Security**: No vulnerabilities introduced

## 🎯 Contribution Areas

### High Priority

- 🐛 **Bug fixes** for critical issues
- ⚡ **Performance optimizations**
- 🔒 **Security improvements**
- 📚 **Documentation enhancements**

### Feature Development

- 🤖 **AI agent development** (new verification algorithms)
- 🌿 **API enhancements** (new endpoints, better error handling)
- 🍃 **UI/UX improvements** (better user experience)
- 🔗 **Blockchain integration** (new smart contract features)

### Community Support

- 💬 **Answer questions** in Discussions
- 👥 **Help other contributors**
- 📢 **Spread the word** about the project
- ⭐ **Star the repository** to show support

## 🏆 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for significant contributions
- **Discord** special roles for active contributors
- **NFT badges** for major milestones (coming soon)

## 📞 Getting Help

- 📚 **Documentation**: [docs.nwu-protocol.com](https://docs.nwu-protocol.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/Garrettc123/nwu-protocol/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Garrettc123/nwu-protocol/discussions)
- 👥 **Discord**: [Join our community](https://discord.gg/nwu-protocol) (coming soon)

## 🔗 Resources

- [Project Roadmap](https://github.com/Garrettc123/nwu-protocol/issues/1)
- [Architecture Documentation](./docs/ARCHITECTURE.md)
- [API Documentation](./docs/API.md)
- [Release Notes](./RELEASE_NOTES.md)

---

## 🙏 Thank You!

Your contributions to open source, large or small, make projects like this possible. Thank you for taking the time to contribute to the NWU Protocol.

Together, we are building the future of verified truth.

---

*"We are the architects of the new world. We build not just for today, but for the preservation of light in the digital age."*  
— **Garrett W. Carrol**