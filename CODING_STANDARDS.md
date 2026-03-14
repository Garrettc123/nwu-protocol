# NWU Protocol Coding Standards

## Overview

This document defines the mandatory coding standards for all code in the NWU Protocol project. These standards are enforced through automated tools and code review processes.

---

## General Principles

### Code Philosophy

1. **Clarity over Cleverness** - Write code that is easy to understand
2. **Consistency** - Follow established patterns
3. **Simplicity** - Prefer simple solutions
4. **Maintainability** - Think about the next developer
5. **Security First** - Security is not optional

### Universal Standards

- **DRY (Don't Repeat Yourself)** - Avoid code duplication
- **KISS (Keep It Simple, Stupid)** - Prefer simple solutions
- **YAGNI (You Aren't Gonna Need It)** - Don't over-engineer
- **SOLID Principles** - Follow object-oriented design principles
- **Boy Scout Rule** - Leave code better than you found it

---

## Language-Specific Standards

### JavaScript/TypeScript

#### Style Guide

Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) with these modifications:

**File Structure**

```typescript
// 1. Imports (grouped and sorted)
import React from 'react';
import { useState } from 'react';
import type { User } from './types';

// 2. Types/Interfaces
interface Props {
  user: User;
  onUpdate: (user: User) => void;
}

// 3. Constants
const MAX_RETRIES = 3;

// 4. Helper functions
function validateUser(user: User): boolean {
  // ...
}

// 5. Main component/function
export function UserProfile({ user, onUpdate }: Props) {
  // ...
}
```

**Naming Conventions**

- **Variables/Functions**: `camelCase` (e.g., `getUserData`)
- **Classes/Components**: `PascalCase` (e.g., `UserProfile`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private fields**: prefix with `_` (e.g., `_internalState`)
- **Interfaces**: prefix with `I` or descriptive name (e.g., `IUser` or `UserProps`)
- **Types**: descriptive name ending in `Type` (e.g., `UserType`)

**Code Quality**

```typescript
// ✅ Good
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// ❌ Bad
function calcTot(i: any) {
  let t = 0;
  for (let x = 0; x < i.length; x++) {
    t += i[x].price;
  }
  return t;
}
```

**Error Handling**

```typescript
// ✅ Good - Explicit error handling
try {
  const data = await fetchUserData(userId);
  return processData(data);
} catch (error) {
  logger.error('Failed to fetch user data', { userId, error });
  throw new UserDataError('Unable to fetch user data', { cause: error });
}

// ❌ Bad - Silent failures
try {
  const data = await fetchUserData(userId);
  return processData(data);
} catch (error) {
  return null; // Silent failure
}
```

**Async/Await**

- Always use `async/await` over raw promises
- Always handle errors in async functions
- Use `Promise.all()` for concurrent operations

```typescript
// ✅ Good
async function loadUserData(userId: string): Promise<UserData> {
  const [user, posts, comments] = await Promise.all([
    fetchUser(userId),
    fetchPosts(userId),
    fetchComments(userId),
  ]);

  return { user, posts, comments };
}
```

#### TypeScript Specifics

**Type Safety**

```typescript
// ✅ Good - Explicit types
interface User {
  id: string;
  name: string;
  email: string;
}

function getUser(id: string): Promise<User> {
  // ...
}

// ❌ Bad - Using 'any'
function getUser(id: any): any {
  // ...
}
```

**Strict Mode**

- Always enable `strict: true` in tsconfig.json
- No `any` types without explicit justification
- Use `unknown` instead of `any` when type is truly unknown
- Prefer union types over `any`

**Linting & Formatting**

- **Linter**: ESLint with TypeScript plugin
- **Formatter**: Prettier
- **Config**: See `.eslintrc.json` and `.prettierrc`

**Required Rules**

- `no-console`: Warn (use proper logging)
- `no-debugger`: Error
- `no-unused-vars`: Error
- `@typescript-eslint/no-explicit-any`: Error
- `@typescript-eslint/explicit-function-return-type`: Warn

---

### Python

#### Style Guide

Follow [PEP 8](https://pep8.org/) and [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

**File Structure**

```python
"""Module docstring describing the purpose of this module."""

# 1. Standard library imports
import os
import sys
from typing import List, Optional

# 2. Third-party imports
import numpy as np
from fastapi import FastAPI

# 3. Local imports
from app.models import User
from app.services import UserService

# 4. Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# 5. Classes
class UserManager:
    """Manages user operations."""

    def __init__(self, db_session):
        self.db_session = db_session

    def get_user(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        pass

# 6. Functions
def calculate_total(items: List[dict]) -> float:
    """Calculate the total price of items."""
    return sum(item['price'] for item in items)
```

**Naming Conventions**

- **Variables/Functions**: `snake_case` (e.g., `get_user_data`)
- **Classes**: `PascalCase` (e.g., `UserProfile`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private methods**: prefix with `_` (e.g., `_internal_method`)
- **Protected methods**: prefix with `_` (e.g., `_protected_method`)

**Type Hints**

```python
# ✅ Good - Type hints everywhere
from typing import List, Optional, Dict

def process_users(
    users: List[User],
    filter_active: bool = True
) -> Dict[str, User]:
    """Process a list of users."""
    pass

# ❌ Bad - No type hints
def process_users(users, filter_active=True):
    pass
```

**Docstrings**

```python
# ✅ Good - Google style docstring
def fetch_user_data(user_id: str, include_posts: bool = False) -> dict:
    """Fetch comprehensive user data.

    Args:
        user_id: The unique identifier for the user
        include_posts: Whether to include user's posts

    Returns:
        A dictionary containing user data

    Raises:
        UserNotFoundError: If the user doesn't exist
        DatabaseError: If database connection fails
    """
    pass
```

**Error Handling**

```python
# ✅ Good - Specific exceptions
try:
    user = User.objects.get(id=user_id)
except User.DoesNotExist:
    logger.error(f"User not found: {user_id}")
    raise UserNotFoundError(f"User {user_id} does not exist")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise

# ❌ Bad - Bare except
try:
    user = User.objects.get(id=user_id)
except:
    return None
```

**Linting & Formatting**

- **Formatter**: Black (line length: 88)
- **Linter**: Flake8
- **Type Checker**: MyPy
- **Import Sorter**: isort

**Required Tools**

```bash
black .
flake8 .
mypy src/
isort .
```

---

### Solidity (Smart Contracts)

#### Style Guide

Follow the [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)

**Contract Structure**

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title NWUToken
 * @dev Implementation of the NWU ERC20 token
 */
contract NWUToken is ERC20, Ownable {
    // 1. Type declarations
    struct Stake {
        uint256 amount;
        uint256 timestamp;
    }

    // 2. State variables
    mapping(address => Stake) public stakes;
    uint256 public constant MAX_SUPPLY = 1000000 * 10**18;

    // 3. Events
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount);

    // 4. Modifiers
    modifier onlyStaker() {
        require(stakes[msg.sender].amount > 0, "Not a staker");
        _;
    }

    // 5. Constructor
    constructor() ERC20("NWU Token", "NWU") {
        _mint(msg.sender, MAX_SUPPLY);
    }

    // 6. External functions
    function stake(uint256 amount) external {
        // ...
    }

    // 7. Public functions
    function getStake(address user) public view returns (uint256) {
        return stakes[user].amount;
    }

    // 8. Internal functions
    function _updateStake(address user, uint256 amount) internal {
        // ...
    }

    // 9. Private functions
    function _calculateReward(uint256 amount) private pure returns (uint256) {
        // ...
    }
}
```

**Naming Conventions**

- **Contracts**: `PascalCase` (e.g., `NWUToken`)
- **Functions**: `camelCase` (e.g., `transferFrom`)
- **Events**: `PascalCase` (e.g., `Transfer`)
- **Modifiers**: `camelCase` (e.g., `onlyOwner`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_SUPPLY`)

**Security Best Practices**

```solidity
// ✅ Good - Checks-Effects-Interactions pattern
function withdraw(uint256 amount) external {
    // Checks
    require(stakes[msg.sender].amount >= amount, "Insufficient stake");

    // Effects
    stakes[msg.sender].amount -= amount;

    // Interactions
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}

// ✅ Good - Use SafeMath (or 0.8+ built-in overflow protection)
// ✅ Good - Explicit visibility
// ✅ Good - Use of events for all state changes
// ✅ Good - Input validation
```

**Testing Requirements**

- Test coverage ≥ 95%
- All functions tested
- Edge cases covered
- Gas optimization verified
- Security audit for mainnet deployment

---

## Security Standards

### Input Validation

```typescript
// ✅ Good - Validate all inputs
function updateUser(data: UpdateUserRequest): User {
  // Validate
  if (!data.email || !isValidEmail(data.email)) {
    throw new ValidationError('Invalid email');
  }
  if (data.age && (data.age < 0 || data.age > 150)) {
    throw new ValidationError('Invalid age');
  }

  // Sanitize
  const sanitized = {
    email: sanitizeEmail(data.email),
    name: sanitizeHtml(data.name),
    age: data.age,
  };

  return updateUserInDb(sanitized);
}
```

### Authentication & Authorization

```python
# ✅ Good - Check permissions
@require_authentication
@require_permission('admin')
def delete_user(user_id: str) -> bool:
    """Delete a user (admin only)."""
    user = get_user(user_id)
    if not user:
        raise UserNotFoundError()

    # Additional checks
    if user.is_super_admin:
        raise ForbiddenError("Cannot delete super admin")

    return user.delete()
```

### Secrets Management

```bash
# ✅ Good - Use environment variables
DATABASE_URL=postgresql://user:pass@localhost/db
API_KEY=${API_KEY}

# ❌ Bad - Hardcoded secrets
DATABASE_URL=postgresql://admin:password123@localhost/db
API_KEY=sk-1234567890abcdef
```

### SQL Injection Prevention

```python
# ✅ Good - Parameterized queries
cursor.execute(
    "SELECT * FROM users WHERE email = %s",
    (user_email,)
)

# ❌ Bad - String concatenation
cursor.execute(
    f"SELECT * FROM users WHERE email = '{user_email}'"
)
```

---

## Testing Standards

### Test Coverage

- **Minimum**: 80% overall coverage
- **Critical paths**: 100% coverage
- **New code**: Must include tests

### Test Structure

```typescript
// ✅ Good - Clear test structure
describe('UserService', () => {
  describe('getUser', () => {
    it('should return user when found', async () => {
      // Arrange
      const userId = '123';
      const expectedUser = { id: userId, name: 'Test User' };

      // Act
      const result = await userService.getUser(userId);

      // Assert
      expect(result).toEqual(expectedUser);
    });

    it('should throw error when user not found', async () => {
      // Arrange
      const userId = 'nonexistent';

      // Act & Assert
      await expect(userService.getUser(userId)).rejects.toThrow(UserNotFoundError);
    });
  });
});
```

### Test Naming

```python
# ✅ Good - Descriptive test names
def test_calculate_total_with_multiple_items_returns_sum():
    pass

def test_calculate_total_with_empty_list_returns_zero():
    pass

def test_calculate_total_with_negative_prices_raises_error():
    pass
```

---

## Documentation Standards

### Code Comments

```typescript
// ✅ Good - Comment the "why", not the "what"
// Use exponential backoff to handle rate limiting
const delay = Math.pow(2, retryCount) * 1000;

// ❌ Bad - Obvious comment
// Set delay to 2 raised to retry count times 1000
const delay = Math.pow(2, retryCount) * 1000;
```

### Function Documentation

```python
# ✅ Good - Comprehensive docstring
def calculate_weighted_average(
    values: List[float],
    weights: List[float]
) -> float:
    """Calculate the weighted average of values.

    The weighted average is calculated as:
    sum(value * weight) / sum(weights)

    Args:
        values: List of numeric values
        weights: List of weights corresponding to each value

    Returns:
        The weighted average as a float

    Raises:
        ValueError: If lengths of values and weights don't match
        ValueError: If sum of weights is zero

    Example:
        >>> calculate_weighted_average([1, 2, 3], [1, 1, 1])
        2.0
    """
    if len(values) != len(weights):
        raise ValueError("Values and weights must have same length")
    if sum(weights) == 0:
        raise ValueError("Sum of weights cannot be zero")

    return sum(v * w for v, w in zip(values, weights)) / sum(weights)
```

---

## Performance Standards

### Big O Complexity

- Document time and space complexity for algorithms
- Avoid O(n²) or worse unless absolutely necessary
- Use appropriate data structures

```python
# ✅ Good - O(1) lookup
user_map = {user.id: user for user in users}
target_user = user_map.get(user_id)

# ❌ Bad - O(n) lookup
target_user = next((u for u in users if u.id == user_id), None)
```

### Database Queries

```python
# ✅ Good - Single query with join
users = User.objects.select_related('profile').filter(active=True)

# ❌ Bad - N+1 query problem
users = User.objects.filter(active=True)
for user in users:
    profile = user.profile  # Triggers additional query
```

---

## Tool Configuration

### ESLint (.eslintrc.json)

```json
{
  "extends": ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "no-console": "warn"
  }
}
```

### Black (pyproject.toml)

```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

### Prettier (.prettierrc)

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

---

## Enforcement

### Automated

- Pre-commit hooks run linters
- CI/CD pipeline enforces standards
- Pull requests blocked if checks fail

### Manual

- Code review checklist includes standards
- Tiger Team spot checks
- Quarterly code quality audits

---

## Resources

- [ESLint Rules](https://eslint.org/docs/rules/)
- [PEP 8](https://pep8.org/)
- [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)
- [OWASP Security Guidelines](https://owasp.org/)

---

**Version**: 1.0  
**Last Updated**: 2026-02-12  
**Owner**: Tiger Team  
**Review Cycle**: Quarterly
