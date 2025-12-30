# NWU Protocol API Examples

This directory contains example scripts demonstrating how to use the NWU Protocol API.

## Prerequisites

1. Start the API server:
```bash
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

2. Install dependencies:
```bash
pip install requests
```

## Running Examples

### API Usage Example

Demonstrates the complete workflow of creating a contribution and submitting verifications:

```bash
python3 examples/api_usage.py
```

This example shows:
1. Checking API health
2. Creating a contribution
3. Submitting an AI agent verification
4. Checking consensus status
5. Viewing contribution status
6. Listing all contributions

## Interactive API Documentation

The API provides interactive documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## More Information

See [API_GUIDE.md](../API_GUIDE.md) for complete API documentation.
