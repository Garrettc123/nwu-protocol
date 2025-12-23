# NWU Protocol - Setup Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for smart contract compilation)
- IPFS daemon
- PostgreSQL 14+

### Installation

```bash
# Clone repository
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python scripts/init_db.py

# Start IPFS daemon
ipfs daemon

# Run application
python main.py
```

## Project Structure

```
nwu-protocol/
├── contracts/          # Smart contracts (Solidity)
├── src/
│   ├── ai/            # AI verification modules
│   ├── blockchain/    # Blockchain interaction
│   ├── ipfs/          # Decentralized storage
│   └── api/           # REST API endpoints
├── tests/             # Test suite
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

## Development

```bash
# Run tests
pytest tests/

# Format code
black src/

# Lint
flake8 src/
```

## Documentation

See [docs/](docs/) for detailed documentation.
