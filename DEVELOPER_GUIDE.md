# Developer Quick Reference - NWU Protocol

## 🚀 Quick Start

### Prerequisites
```bash
# Required
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose

# Optional (for full features)
- OpenAI API Key
- Stripe API Keys
- Ethereum RPC URL
```

### One-Command Setup
```bash
./deploy.sh
```

### Manual Setup
```bash
# 1. Clone and configure
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol
cp .env.example .env

# 2. Start services
docker-compose up -d

# 3. Run migrations
cd backend && alembic upgrade head

# 4. Start backend
uvicorn app.main:app --reload

# 5. Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

## 🔐 Authentication Flow

### 1. Connect Wallet
```python
POST /api/v1/auth/connect
{
  "address": "0x1234..."
}

Response:
{
  "nonce": "abc123...",
  "message": "Sign this message to authenticate...",
  "address": "0x1234..."
}
```

### 2. Sign Message
```javascript
// Client-side (Web3)
const signature = await web3.eth.personal.sign(message, address);
```

### 3. Verify & Get Token
```python
POST /api/v1/auth/verify
{
  "address": "0x1234...",
  "signature": "0xabc...",
  "nonce": "abc123..."
}

Response:
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "address": "0x1234...",
  "expires_in": 86400
}
```

### 4. Use Token
```python
GET /api/v1/payments/subscriptions/current
Headers:
  Authorization: Bearer eyJ0eXAi...
```

## 📝 Common Patterns

### Create a New API Endpoint

```python
# backend/app/api/my_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..api.payments import get_current_user  # For auth

router = APIRouter(prefix="/api/v1/my-feature", tags=["my-feature"])

@router.get("/")
async def get_data(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)  # JWT auth
):
    """Get data for authenticated user."""
    return {"data": "example"}
```

### Add to Main App
```python
# backend/app/main.py
from .api.my_feature import router as my_feature_router

app.include_router(my_feature_router)
```

### Create a New Service

```python
# backend/app/services/my_service.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MyService:
    """Service for handling X."""

    def __init__(self):
        """Initialize service."""
        self.client = None

    async def do_something(self, param: str) -> Optional[str]:
        """Do something with param."""
        try:
            # Implementation
            logger.info(f"Processed: {param}")
            return result
        except Exception as e:
            logger.error(f"Failed to process: {e}")
            return None

# Global instance
my_service = MyService()
```

### Export Service
```python
# backend/app/services/__init__.py
from .my_service import my_service, MyService

__all__ = [
    # ... existing exports
    'my_service',
    'MyService',
]
```

### Create Database Model

```python
# backend/app/models.py
class MyModel(Base):
    __tablename__ = "my_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="my_models")
```

### Create Migration
```bash
cd backend
alembic revision --autogenerate -m "Add my_models table"
alembic upgrade head
```

### Write Tests

```python
# tests/test_my_feature.py
import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_my_endpoint():
    """Test my endpoint."""
    response = client.get("/api/v1/my-feature/")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_my_service():
    """Test my service."""
    from app.services import my_service
    result = await my_service.do_something("test")
    assert result is not None
```

## 🛠️ Common Tasks

### Run Tests
```bash
# All tests
cd backend && pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_my_feature.py

# Specific test
pytest tests/test_my_feature.py::test_my_endpoint -v
```

### Database Operations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history
```

### Docker Operations
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop all
docker-compose down

# Rebuild
docker-compose up -d --build
```

### Code Quality
```bash
# Format code
black backend/app

# Sort imports
isort backend/app

# Type checking
mypy backend/app

# Linting
flake8 backend/app
```

## 🐛 Debugging

### Common Issues

#### Import Errors
```bash
# Solution: Install in editable mode
pip install -e .
```

#### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U nwu_user -d nwu_db
```

#### Redis Connection Failed
```bash
# Check if Redis is running
docker ps | grep redis

# Test connection
redis-cli ping
```

#### JWT Token Invalid
```bash
# Check if JWT_SECRET_KEY is set consistently
python -c "from app.config import settings; print(settings.jwt_secret_key)"
```

### Debug Mode
```python
# backend/.env
DEBUG=true

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Useful Commands

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# RabbitMQ management
open http://localhost:15672
```

### Database Queries
```python
# In Python shell
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total users: {len(users)}")
```

### Check Service Status
```bash
make status
# Or
docker-compose ps
```

## 🔑 Environment Variables

### Required for Production
```bash
JWT_SECRET_KEY="your-256-bit-secret"
SECRET_KEY="your-256-bit-secret"
DATABASE_URL="postgresql://user:pass@host/db"
```

### Optional Features
```bash
# Stripe Payments
STRIPE_API_KEY="sk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."

# OpenAI
OPENAI_API_KEY="sk-..."

# Blockchain
ETH_RPC_URL="https://mainnet.infura.io/v3/..."
CONTRACT_ADDRESS="0x..."
```

## 📚 Code Conventions

### Import Order
```python
# 1. Standard library
import os
import sys

# 2. Third-party packages
from fastapi import APIRouter
from sqlalchemy.orm import Session

# 3. Local application (use relative imports)
from ..models import User
from ..services import auth_service
```

### Naming Conventions
```python
# Classes: PascalCase
class UserManager:

# Functions/Methods: snake_case
def get_user_by_id():

# Constants: UPPER_SNAKE_CASE
API_VERSION = "v1"

# Variables: snake_case
user_count = 10
```

### Error Handling
```python
# Always specify exception type
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### Docstrings
```python
def my_function(param: str) -> dict:
    """
    Short description.

    Longer description if needed.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: If param is invalid
    """
    pass
```

## 🔗 Useful Links

- **API Documentation**: http://localhost:8000/docs
- **Repository**: https://github.com/Garrettc123/nwu-protocol
- **Security Guide**: [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md)
- **Implementation Report**: [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md)
- **Health Report**: [SYSTEM_HEALTH_REPORT.md](SYSTEM_HEALTH_REPORT.md)

## 💡 Tips

1. **Use make commands**: `make help` for all available commands
2. **Check logs frequently**: `docker-compose logs -f`
3. **Write tests first**: TDD helps catch issues early
4. **Use type hints**: Helps catch bugs at development time
5. **Keep it simple**: Don't over-engineer solutions
6. **Document as you go**: Future you will thank present you

## 🆘 Getting Help

1. Check existing documentation
2. Search GitHub issues
3. Check application logs
4. Review test examples
5. Create detailed bug report with:
   - Environment details
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

---

**Last Updated**: 2026-03-12
**Version**: 1.0.0
