# Payment Integration Documentation

## Overview

The NWU Protocol now includes a comprehensive payment integration system using Stripe for enterprise features, subscriptions, and API key management. This enables monetization of the platform through tiered subscription plans and usage-based billing.

## Features

### 🎯 Core Capabilities

1. **Subscription Management**
   - Three tiers: Free, Pro, Enterprise
   - Stripe-powered recurring billing
   - Automatic API key generation
   - Rate limiting per tier

2. **API Key Management**
   - Secure key generation and storage (SHA-256 hashing)
   - Tier-based access control
   - Usage tracking and analytics
   - Key expiration and revocation

3. **Payment Processing**
   - One-time payment intents
   - Subscription billing
   - Payment history tracking
   - Stripe webhook integration

4. **Usage Metering**
   - Track API usage per subscription
   - Foundation for usage-based billing
   - Analytics and reporting

## Subscription Tiers

### Free Tier

- **Price:** $0/month
- **Rate Limit:** 100 requests/day
- **Features:**
  - Basic verification
  - Community support
  - Standard API access

### Pro Tier

- **Price:** $99/month
- **Rate Limit:** 10,000 requests/day
- **Features:**
  - Advanced verification
  - Priority support
  - Custom AI agents
  - Analytics dashboard
  - Extended API access

### Enterprise Tier

- **Price:** $999/month
- **Rate Limit:** 100,000 requests/day
- **Features:**
  - Premium verification
  - 24/7 dedicated support
  - Custom integrations
  - SLA guarantee
  - Advanced analytics
  - White-label options
  - Unlimited API access

## API Endpoints

### Subscription Management

#### Create Subscription

```http
POST /api/v1/payments/subscriptions/create
```

**Request Body:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "tier": "pro",
  "stripe_price_id": "price_xxxxxxxxxxxx"
}
```

**Response:**

```json
{
  "subscription_id": 1,
  "tier": "pro",
  "status": "active",
  "api_key": "nwu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "rate_limit": 10000,
  "current_period_end": "2026-03-15T20:17:00.000Z"
}
```

#### Get Subscription

```http
GET /api/v1/payments/subscriptions/{address}
```

**Response:**

```json
{
  "subscription_id": 1,
  "tier": "pro",
  "status": "active",
  "rate_limit": 10000,
  "current_period_start": "2026-02-15T20:17:00.000Z",
  "current_period_end": "2026-03-15T20:17:00.000Z",
  "cancel_at_period_end": false
}
```

#### Cancel Subscription

```http
POST /api/v1/payments/subscriptions/{subscription_id}/cancel
```

**Query Parameters:**

- `immediately` (optional): Cancel immediately vs at period end

**Response:**

```json
{
  "message": "Subscription canceled successfully",
  "immediately": false
}
```

### Payment Management

#### Create Payment Intent

```http
POST /api/v1/payments/payment-intent/create
```

**Request Body:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "amount": 99.0,
  "description": "Pro subscription - Monthly"
}
```

**Response:**

```json
{
  "payment_id": 1,
  "client_secret": "pi_xxxxxxxxxxxx_secret_xxxxxxxxxxxx",
  "amount": 99.0,
  "currency": "usd"
}
```

#### Get Payment History

```http
GET /api/v1/payments/payments/{address}
```

**Query Parameters:**

- `skip` (optional): Pagination offset
- `limit` (optional): Number of results (max 100)

**Response:**

```json
{
  "payments": [
    {
      "id": 1,
      "amount": 99.0,
      "currency": "usd",
      "status": "succeeded",
      "description": "Pro subscription - Monthly",
      "created_at": "2026-02-15T20:17:00.000Z"
    }
  ],
  "total": 1
}
```

### API Key Management

#### Create API Key

```http
POST /api/v1/payments/api-keys/create
```

**Request Body:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "name": "Production API Key",
  "tier": "pro"
}
```

**Response:**

```json
{
  "id": 1,
  "key": "nwu_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "prefix": "nwu_xxxxxxxx",
  "name": "Production API Key",
  "tier": "pro",
  "expires_at": "2027-02-15T20:17:00.000Z"
}
```

⚠️ **Important:** The full API key is only returned once. Store it securely!

#### List API Keys

```http
GET /api/v1/payments/api-keys/{address}
```

**Response:**

```json
{
  "keys": [
    {
      "id": 1,
      "name": "Production API Key",
      "prefix": "nwu_xxxxxxxx",
      "tier": "pro",
      "is_active": true,
      "last_used_at": "2026-02-15T19:00:00.000Z",
      "expires_at": "2027-02-15T20:17:00.000Z",
      "created_at": "2026-02-15T20:17:00.000Z"
    }
  ]
}
```

#### Revoke API Key

```http
DELETE /api/v1/payments/api-keys/{key_id}?address={address}
```

**Response:**

```json
{
  "message": "API key revoked successfully"
}
```

### Pricing Information

#### Get Pricing

```http
GET /api/v1/payments/pricing
```

**Response:**

```json
{
  "tiers": [
    {
      "name": "free",
      "display_name": "Free",
      "price": 0,
      "currency": "usd",
      "billing_period": "monthly",
      "features": [...],
      "rate_limit": 100
    },
    {
      "name": "pro",
      "display_name": "Pro",
      "price": 99,
      "currency": "usd",
      "billing_period": "monthly",
      "features": [...],
      "rate_limit": 10000
    },
    {
      "name": "enterprise",
      "display_name": "Enterprise",
      "price": 999,
      "currency": "usd",
      "billing_period": "monthly",
      "features": [...],
      "rate_limit": 100000
    }
  ]
}
```

### Webhook Handling

#### Stripe Webhook

```http
POST /api/v1/payments/webhook
```

**Headers:**

- `stripe-signature`: Stripe webhook signature for verification

This endpoint handles Stripe webhook events:

- `payment_intent.succeeded` - Payment successful
- `payment_intent.payment_failed` - Payment failed
- `customer.subscription.updated` - Subscription updated
- `customer.subscription.deleted` - Subscription canceled

## Database Schema

### Subscriptions Table

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    tier ENUM('FREE', 'PRO', 'ENTERPRISE'),
    stripe_subscription_id VARCHAR(100) UNIQUE,
    stripe_customer_id VARCHAR(100),
    status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN,
    api_key VARCHAR(100) UNIQUE,
    rate_limit INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Payments Table

```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    stripe_payment_id VARCHAR(100) UNIQUE,
    stripe_invoice_id VARCHAR(100),
    amount FLOAT,
    currency VARCHAR(10),
    status ENUM('PENDING', 'SUCCEEDED', 'FAILED', 'REFUNDED', 'CANCELED'),
    description TEXT,
    metadata TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### API Keys Table

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) UNIQUE,
    name VARCHAR(100),
    prefix VARCHAR(20),
    tier ENUM('FREE', 'PRO', 'ENTERPRISE'),
    is_active BOOLEAN,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP
);
```

### Usage Records Table

```sql
CREATE TABLE usage_records (
    id INTEGER PRIMARY KEY,
    subscription_id INTEGER REFERENCES subscriptions(id),
    endpoint VARCHAR(255),
    request_count INTEGER,
    record_date TIMESTAMP,
    created_at TIMESTAMP
);
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Payment Integration (Stripe)
STRIPE_API_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here

# Subscription Tiers Rate Limits (requests per day)
SUBSCRIPTION_TIER_FREE_RATE_LIMIT=100
SUBSCRIPTION_TIER_PRO_RATE_LIMIT=10000
SUBSCRIPTION_TIER_ENTERPRISE_RATE_LIMIT=100000
```

### Stripe Setup

1. **Create Stripe Account**
   - Sign up at https://stripe.com
   - Complete account verification

2. **Get API Keys**
   - Navigate to Developers > API Keys
   - Copy your Secret Key and Publishable Key
   - Store securely in `.env`

3. **Create Products and Prices**

   ```bash
   # Pro Tier
   stripe products create \
     --name "NWU Pro Subscription" \
     --description "10,000 requests/day with advanced features"

   stripe prices create \
     --product prod_xxxxxxxxxxxx \
     --unit-amount 9900 \
     --currency usd \
     --recurring[interval]=month
   ```

4. **Set Up Webhooks**
   - Go to Developers > Webhooks
   - Add endpoint: `https://your-domain.com/api/v1/payments/webhook`
   - Select events:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
   - Copy webhook signing secret

5. **Test with Stripe CLI** (Development)
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/payments/webhook
   ```

## Migration

To apply the payment database schema:

```bash
cd backend
alembic upgrade head
```

This will run migration `003_add_payment_tables.py`.

## Security Considerations

### API Key Security

- API keys are hashed using SHA-256 before storage
- Full keys are only displayed once at creation
- Keys can be revoked at any time
- Keys have expiration dates (1 year default)

### Payment Security

- All payment processing handled by Stripe
- PCI compliance managed by Stripe
- No credit card data stored in our database
- Webhook signatures verified for authenticity

### Rate Limiting

- Enforced per subscription tier
- Prevents abuse of API resources
- Can be adjusted per tier in configuration

## Usage Examples

### Frontend Integration

#### Subscribe to Pro Tier

```javascript
// 1. Create subscription on backend
const response = await fetch('/api/v1/payments/subscriptions/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    address: userAddress,
    tier: 'pro',
    stripe_price_id: 'price_xxxxxxxxxxxx',
  }),
});

const { subscription_id, api_key } = await response.json();

// 2. Store API key securely
localStorage.setItem('nwu_api_key', api_key);
```

#### Make API Request with Key

```javascript
const apiKey = localStorage.getItem('nwu_api_key');

const response = await fetch('/api/v1/contributions', {
  headers: {
    'X-API-Key': apiKey,
    'Content-Type': 'application/json',
  },
});
```

### Backend Integration

#### Verify API Key Middleware

```python
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Verify API key and enforce rate limits."""
    from app.services.payment_service import payment_service

    api_key_obj = await payment_service.verify_api_key(db, x_api_key)

    if not api_key_obj:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )

    # Check rate limits (implement your rate limiting logic)
    # ...

    return api_key_obj

# Use in endpoint
@router.get("/protected")
async def protected_endpoint(
    api_key: APIKey = Depends(verify_api_key)
):
    return {"message": f"Authenticated with tier: {api_key.tier.value}"}
```

## Testing

### Test Mode

Use Stripe test keys for development:

- Test Secret Key: `sk_test_...`
- Test Publishable Key: `pk_test_...`

### Test Cards

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Requires Auth: 4000 0025 0000 3155
```

### Example Test

```python
import pytest
from app.services.payment_service import payment_service

@pytest.mark.asyncio
async def test_create_subscription(db_session, test_user):
    """Test subscription creation."""
    subscription = await payment_service.create_subscription(
        db_session,
        test_user,
        SubscriptionTier.PRO,
        "price_test_xxxxx"
    )

    assert subscription is not None
    assert subscription.tier == SubscriptionTier.PRO
    assert subscription.api_key is not None
    assert subscription.rate_limit == 10000
```

## Troubleshooting

### Common Issues

#### 1. Stripe Not Configured

**Error:** `Stripe API key not configured`
**Solution:** Add `STRIPE_API_KEY` to `.env` file

#### 2. Webhook Signature Failed

**Error:** `Webhook handling failed`
**Solution:** Verify `STRIPE_WEBHOOK_SECRET` is correct

#### 3. Payment Intent Failed

**Error:** `Failed to create payment intent`
**Solution:** Check Stripe dashboard for error details

#### 4. API Key Invalid

**Error:** `Invalid or expired API key`
**Solution:** Generate a new API key or check expiration date

## Support

For payment integration issues:

1. Check Stripe Dashboard for detailed logs
2. Review application logs for error messages
3. Test with Stripe CLI in development
4. Contact support with transaction IDs

## Roadmap

Future enhancements planned:

- [ ] Usage-based billing (metered pricing)
- [ ] Annual subscription discounts
- [ ] Team/organization accounts
- [ ] Invoice customization
- [ ] Payment method updates
- [ ] Refund processing
- [ ] Credit system
- [ ] Partner revenue sharing

---

## Summary

The NWU Protocol payment integration provides a robust, secure, and scalable foundation for monetizing the platform through subscription tiers and enterprise features. The system is built on Stripe's proven infrastructure and follows best practices for payment processing, security, and compliance.

For questions or support, refer to the main documentation or contact the development team.
