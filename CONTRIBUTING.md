# Contributing to NWU Protocol

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the NWU Protocol project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites
- Git
- Node.js 18+ (for backend/frontend/contracts)
- Python 3.9+ (for AI agents)
- Docker (optional, for services)

### Setup Development Environment

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/nwu-protocol.git
   cd nwu-protocol
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Install Dependencies**
   ```bash
   # Backend
   cd backend && npm install
   
   # Frontend
   cd ../frontend && npm install
   
   # Contracts
   cd ../contracts && npm install
   
   # Agents
   cd ../agents && pip install -r requirements.txt
   ```

4. **Start Development Services**
   ```bash
   docker-compose up -d
   ```

## Development Workflow

### Branch Naming Convention
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `perf/description` - Performance improvements

### Commit Message Format

We follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style changes (formatting, semicolons, etc.)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test updates
- `chore:` Dependency updates, tool configs

**Examples:**
```
feat(backend): add user authentication

Implemented JWT-based authentication with:
- Login endpoint
- Token refresh logic
- Protected middleware

Closes #123
```

```
fix(frontend): resolve navbar spacing issue

Adjusted padding on mobile devices.

Fixes #456
```

## Code Standards

### Backend (Node.js/Express)
- Use async/await for asynchronous operations
- Follow ESLint configuration
- Write unit tests for all functions
- Document API endpoints with JSDoc

```javascript
/**
 * Get user by ID
 * @param {string} userId - The user's ID
 * @returns {Promise<Object>} User object
 * @throws {Error} If user not found
 */
async function getUserById(userId) {
  // Implementation
}
```

### Frontend (Next.js/React)
- Use functional components with hooks
- Follow Tailwind CSS conventions
- Write prop validation with TypeScript
- Create reusable component patterns

```typescript
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
}

export default function UserProfile({ userId, onUpdate }: UserProfileProps) {
  // Implementation
}
```

### Smart Contracts (Solidity)
- Follow Solidity Style Guide
- Use OpenZeppelin libraries for standards
- Include comprehensive comments
- Test all functions thoroughly

```solidity
/// @notice Transfer tokens to a recipient
/// @param to The recipient address
/// @param amount The amount to transfer
/// @return success Whether the transfer succeeded
function transfer(address to, uint256 amount) public returns (bool success) {
    // Implementation
}
```

### AI Agents (Python)
- Follow PEP 8 style guide
- Use type hints
- Document functions with docstrings
- Write unit tests with pytest

```python
def verify_contribution(content: str) -> dict[str, Any]:
    """
    Verify code quality and originality of a contribution.
    
    Args:
        content: The contribution content to verify
    
    Returns:
        Dictionary with verification results including score and approved status
    
    Raises:
        ValueError: If content is empty or invalid
    """
    # Implementation
```

## Testing

### Backend Tests
```bash
cd backend
npm test
npm run test:coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Contract Tests
```bash
cd contracts
npm run test
npm run test:coverage
```

### Agent Tests
```bash
cd agents
pytest
pytest --cov
```

### Test Coverage Requirements
- Minimum 80% code coverage
- All critical paths must be tested
- Write tests for edge cases

## Pull Request Process

1. **Update Documentation**
   - Update README if adding features
   - Add API documentation for new endpoints
   - Update component docs for UI changes

2. **Run Tests**
   ```bash
   npm test
   npm run lint
   npm run build
   ```

3. **Create PR**
   - Clear title describing the change
   - Reference related issues
   - Add description of changes
   - Include testing information

4. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Related Issues
   Fixes #123
   Related to #456
   
   ## Testing
   - [ ] Added tests
   - [ ] All tests pass
   - [ ] Manual testing done
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex logic
   - [ ] Documentation updated
   - [ ] No new warnings generated
   ```

5. **Code Review**
   - Address reviewer feedback promptly
   - Request re-review after changes
   - Be open to suggestions

6. **Merge**
   - Squash commits for cleaner history
   - Ensure all CI checks pass
   - Delete feature branch after merge

## Documentation

### Writing Docs
- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep docs in sync with code

### Documentation Structure
```
docs/
├── architecture/
│   ├── system-design.md
│   └── data-flow.md
├── api/
│   ├── backend-api.md
│   └── contract-interface.md
├── guides/
│   ├── setup.md
│   ├── deployment.md
│   └── troubleshooting.md
└── components/
    ├── frontend-components.md
    └── smart-contracts.md
```

## Reporting Issues

Use the provided issue templates:
- **Bug Report** - For reporting bugs
- **Feature Request** - For suggesting features

Include:
- Clear title
- Detailed description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment information
- Screenshots/logs if applicable

## Project Maintenance

### Maintainers
- @Garrettc123 (Project Lead)

### Review Process
1. Automated checks (CI/CD)
2. Code review by maintainers
3. Approval by at least one maintainer
4. Merge when all checks pass

## Recognition

All contributors will be:
- Added to CONTRIBUTORS.md
- Credited in release notes
- Recognized in the community

## Questions?

Reach out through:
- GitHub Issues - for bugs/features
- GitHub Discussions - for questions
- Discord - for real-time chat

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to NWU Protocol! 🚀
