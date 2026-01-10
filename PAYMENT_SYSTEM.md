# Payment System Integration

This document explains how the NWU Protocol payment system works for generating real-world currency.

## Overview

The NWU Protocol generates real-world currency through multiple revenue streams:

1. **Token Sales** - Users purchase NWU tokens with USD via Stripe
2. **Subscriptions** - Recurring revenue from API access plans
3. **Transaction Fees** - Fees on withdrawals and payouts
4. **Verification Services** - Enterprise API access fees

## Architecture

```
┌─────────────┐
│   Frontend  │
│   (User)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│    Payment API Endpoints        │
│  /api/v1/payments/*             │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│    Payment Service              │
│    (payment_service.py)         │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│         Stripe API              │
│  (Payment Processing)           │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│    Smart Contracts              │
│  (Token Minting/Distribution)   │
└─────────────────────────────────┘
```

## API Endpoints

### 1. Create Payment Intent

Create a one-time payment for purchasing tokens or services.

**Endpoint:** `POST /api/v1/payments/create-payment-intent`

**Request:**
```json
{
  "amount": 100.00,
  "customer_email": "user@example.com",
  "token_amount": 10000,
  "metadata": {
    "user_id": "123",
    "wallet_address": "0x..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "client_secret": "pi_xxx_secret_xxx",
    "payment_intent_id": "pi_xxx",
    "amount": 100.00,
    "currency": "usd"
  }
}
```

### 2. Create Subscription

Set up recurring payments for API access.

**Endpoint:** `POST /api/v1/payments/create-subscription`

**Request:**
```json
{
  "customer_email": "user@example.com",
  "plan": "premium",
  "metadata": {
    "organization": "Acme Corp"
  }
}
```

**Plans:**
- `basic` - $49/month for individual developers
- `premium` - $149/month for small teams
- `enterprise` - $499/month for large organizations

**Response:**
```json
{
  "success": true,
  "data": {
    "subscription_id": "sub_xxx",
    "customer_id": "cus_xxx",
    "status": "active",
    "current_period_end": 1234567890
  }
}
```

### 3. Create Payout

Send rewards to contributors in real currency.

**Endpoint:** `POST /api/v1/payments/create-payout`

**Request:**
```json
{
  "amount": 50.00,
  "destination": "ba_xxx",
  "metadata": {
    "contributor_id": "456",
    "contribution_id": "789"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payout_id": "po_xxx",
    "amount": 50.00,
    "currency": "usd",
    "status": "pending",
    "arrival_date": 1234567890
  },
  "fee_info": {
    "gross_amount": 50.00,
    "fee_percentage": 2.5,
    "fee_amount": 1.25,
    "net_amount": 48.75
  }
}
```

### 4. Webhook Handler

Receive notifications about payment events.

**Endpoint:** `POST /api/v1/payments/webhook`

**Stripe will send events for:**
- `payment_intent.succeeded` - Payment completed
- `payment_intent.payment_failed` - Payment failed
- `customer.subscription.created` - New subscription
- `customer.subscription.deleted` - Subscription cancelled

### 5. Calculate Token Price

Get USD price for a number of tokens.

**Endpoint:** `POST /api/v1/payments/calculate-token-price`

**Request:**
```json
{
  "token_amount": 1000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token_amount": 1000,
    "usd_price": 10.00,
    "price_per_token": 0.01
  }
}
```

### 6. Calculate Token Amount

Get number of tokens for a USD amount.

**Endpoint:** `POST /api/v1/payments/calculate-token-amount`

**Request:**
```json
{
  "usd_amount": 50.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "usd_amount": 50.00,
    "token_amount": 5000,
    "price_per_token": 0.01
  }
}
```

### 7. Get Payment Config

Get public configuration for the frontend.

**Endpoint:** `GET /api/v1/payments/config`

**Response:**
```json
{
  "success": true,
  "data": {
    "publishable_key": "pk_test_xxx",
    "token_price_usd": "0.01",
    "min_withdrawal_amount": "10.00",
    "withdrawal_fee_percentage": "2.5",
    "plans": {
      "basic": {
        "name": "Basic",
        "description": "For individual developers",
        "price": "$49/month"
      },
      "premium": {
        "name": "Premium",
        "description": "For small teams",
        "price": "$149/month"
      },
      "enterprise": {
        "name": "Enterprise",
        "description": "For large organizations",
        "price": "$499/month"
      }
    }
  }
}
```

## Token Economics

- **Token Price:** $0.01 per NWU token
- **Minimum Purchase:** $1.00 (100 tokens)
- **Maximum Supply:** 10 billion tokens
- **Initial Supply:** 1 billion tokens

## Fee Structure

### Transaction Fees
- **Withdrawal Fee:** 2.5% of withdrawal amount
- **Minimum Withdrawal:** $10.00
- **Payment Processing:** Stripe fees (2.9% + $0.30 per transaction)

### Revenue Split
- Platform: 70%
- Contributors: 25%
- Community fund: 5%

## Payment Flow Examples

### Example 1: User Purchases Tokens

1. User requests to buy 1000 NWU tokens
2. API calculates price: 1000 × $0.01 = $10.00
3. Payment intent created via Stripe
4. User completes payment on frontend
5. Webhook confirms payment succeeded
6. Backend mints 1000 NWU tokens
7. Tokens transferred to user's wallet

### Example 2: Contributor Receives Rewards

1. AI agent verifies contribution with quality score 85
2. Backend calculates reward: 100 NWU × (85/70) = ~121 NWU
3. Reward allocated to contributor's account
4. Contributor requests withdrawal: 121 NWU = $1.21
5. Fee calculated: $1.21 × 2.5% = $0.03
6. Net payout: $1.18
7. Payout created via Stripe to contributor's bank

### Example 3: Enterprise Subscription

1. Company signs up for Enterprise plan
2. Subscription created: $499/month
3. Stripe charges card monthly
4. Company receives API access with higher limits
5. Webhook updates subscription status
6. Company can use verification services

## Frontend Integration

### Step 1: Load Stripe.js

```html
<script src="https://js.stripe.com/v3/"></script>
```

### Step 2: Initialize Stripe

```javascript
// Get publishable key from config endpoint
const config = await fetch('/api/v1/payments/config').then(r => r.json());
const stripe = Stripe(config.data.publishable_key);
```

### Step 3: Create Payment Intent

```javascript
const response = await fetch('/api/v1/payments/create-payment-intent', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    token_amount: 1000,
    customer_email: 'user@example.com'
  })
});

const { client_secret } = await response.json();
```

### Step 4: Confirm Payment

```javascript
const { error } = await stripe.confirmCardPayment(client_secret, {
  payment_method: {
    card: cardElement,
    billing_details: {
      email: 'user@example.com'
    }
  }
});

if (error) {
  console.error(error.message);
} else {
  console.log('Payment succeeded!');
}
```

## Security Considerations

1. **API Keys:** Never expose secret keys in frontend code
2. **Webhook Signatures:** Always verify Stripe webhook signatures
3. **Rate Limiting:** Implement rate limits on payment endpoints
4. **Input Validation:** Validate all amounts and parameters
5. **SSL/HTTPS:** Always use HTTPS in production
6. **PCI Compliance:** Never handle raw card data directly

## Testing

### Test Mode
Use Stripe test keys for development:
- `sk_test_...` for secret key
- `pk_test_...` for publishable key

### Test Cards
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Require 3D Secure: `4000 0025 0000 3155`

### Test Webhooks
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8000/api/v1/payments/webhook

# Trigger test events
stripe trigger payment_intent.succeeded
```

## Monitoring

Track these key metrics:
- Total revenue
- Payment success rate
- Average transaction value
- Active subscriptions
- Payout volume
- Failed payments
- Webhook delivery rate

## Support

For issues or questions:
- GitHub Issues: https://github.com/Garrettc123/nwu-protocol/issues
- Documentation: See PRODUCTION_DEPLOYMENT.md
- Stripe Support: https://support.stripe.com
