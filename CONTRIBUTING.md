# Contributing to NWU Protocol

Thank you for considering contributing to the NWU Protocol!

## Development Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## Code Standards

- Follow PEP 8 for Python code
- Write comprehensive tests for new features
- Update documentation as needed
- Add docstrings to all functions/classes
- Keep commits atomic and well-described

## Smart Contract Guidelines

- Follow Solidity style guide
- Write extensive tests for all contract functions
- Include NatSpec comments
- Run security audits before mainnet deployment

## Testing Requirements

```bash
# Run full test suite
pytest tests/ -v --cov=src

# Run specific test module
pytest tests/test_blockchain.py

# Run contract tests
brownie test
```

## Pull Request Process

1. Update README.md with details of changes
2. Ensure all tests pass
3. Update documentation
4. Request review from maintainers
5. Address review feedback

## Security

Report security vulnerabilities to security@garrettcarroll.dev

## Questions?

Open an issue for discussion!
