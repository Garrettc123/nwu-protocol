# 🚀 Quick Start: Deploy and Generate Revenue

This guide will get your NWU Protocol deployed and generating real-world currency in under 30 minutes.

## 🎯 Goal

Deploy a fully functional system that:
- ✅ Accepts payments from users via credit card
- ✅ Sells NWU tokens for real USD
- ✅ Processes recurring subscriptions
- ✅ Pays out rewards to contributors
- ✅ Generates revenue through multiple streams

## 📋 Prerequisites (5 minutes)

1. **Stripe Account** (FREE)
   - Sign up at https://stripe.com
   - Get your API keys from Dashboard → Developers → API keys
   - You can start with test mode - no credit card required!

2. **OpenAI API Key** (Optional for AI features)
   - Sign up at https://platform.openai.com
   - Get API key from API keys page

3. **Infura Account** (FREE for testnet)
   - Sign up at https://infura.io
   - Create a project
   - Get your Sepolia RPC URL

## ⚡ Quick Deploy (3 steps)

### Step 1: Clone and Configure (2 minutes)

```bash
# Clone the repository
git clone https://github.com/Garrettc123/nwu-protocol.git
cd nwu-protocol

# Copy environment template
cp .env.example .env

# Edit .env with your keys
nano .env  # or use your favorite editor
```

**Add these keys to .env:**
```bash
# Minimum required for payments
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET

# For blockchain features (can use test values)
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
PRIVATE_KEY=YOUR_WALLET_PRIVATE_KEY
```

### Step 2: Deploy Smart Contracts (5 minutes)

```bash
cd contracts
npm install
npm run compile
npm run test

# Deploy to Sepolia testnet (FREE - no real ETH needed)
npm run deploy:sepolia

# Save the contract addresses that are printed
```

**Note:** You'll get some Sepolia test ETH from faucets like:
- https://sepoliafaucet.com
- https://sepolia-faucet.pk910.de

### Step 3: Start the Backend (2 minutes)

```bash
cd ..

# Option A: Using Docker (Recommended)
docker-compose up -d

# Option B: Direct Python
pip install -r backend/requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

## ✅ Verify It's Working (2 minutes)

1. **Check API is running:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy","service":"nwu-protocol"}
   ```

2. **Check payment config:**
   ```bash
   curl http://localhost:8000/api/v1/payments/config
   # Should return Stripe publishable key and pricing info
   ```

3. **Test token price calculation:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/payments/calculate-token-price \
     -H "Content-Type: application/json" \
     -d '{"token_amount": 1000}'
   # Should return: {"success":true,"data":{"token_amount":1000,"usd_price":10.0,...}}
   ```

## 💰 Start Generating Revenue (3 methods)

### Method 1: Token Sales

Users buy NWU tokens with credit card:

```bash
# 1. Create payment intent for 1000 tokens ($10)
curl -X POST http://localhost:8000/api/v1/payments/create-payment-intent \
  -H "Content-Type: application/json" \
  -d '{
    "token_amount": 1000,
    "customer_email": "customer@example.com"
  }'

# Returns: client_secret for frontend payment form
```

**Revenue:** $0.01 per token sold

### Method 2: Subscriptions

Companies pay monthly for API access:

```bash
# Create enterprise subscription ($499/month)
curl -X POST http://localhost:8000/api/v1/payments/create-subscription \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "cto@company.com",
    "plan": "enterprise"
  }'
```

**Revenue:** 
- Basic: $49/month
- Premium: $149/month  
- Enterprise: $499/month

### Method 3: Transaction Fees

Earn 2.5% on every contributor withdrawal:

```bash
# When contributor withdraws $100
curl -X POST http://localhost:8000/api/v1/payments/create-payout \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 100.00,
    "destination": "ba_1234567890"
  }'

# You keep $2.50 as fee, pay out $97.50
```

**Revenue:** 2.5% of every withdrawal

## 🌐 Production Deployment (Optional)

For production deployment with real money:

1. **Switch to Stripe Live Mode:**
   - Get live keys from Stripe dashboard
   - Update .env with `sk_live_` and `pk_live_` keys

2. **Deploy to Mainnet:**
   ```bash
   cd contracts
   npm run deploy:mainnet
   # ⚠️ This costs real ETH for gas!
   ```

3. **Deploy Backend:**
   - Vercel: `vercel --prod`
   - AWS/GCP: See PRODUCTION_DEPLOYMENT.md
   - Docker: Use docker-compose.yml

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for full details.

## 📊 Track Your Revenue

### Via API

```bash
# Get payment stats (to be implemented)
curl http://localhost:8000/api/v1/stats/revenue
```

### Via Stripe Dashboard

1. Go to https://dashboard.stripe.com
2. View:
   - Payments → See all transactions
   - Billing → See subscriptions
   - Payouts → See money being transferred
   - Reports → Detailed revenue analytics

## 🔧 Customize Pricing

Edit `.env` to change prices:

```bash
# Token price (default: $0.01)
NWU_TOKEN_PRICE_USD=0.01

# Withdrawal settings
MIN_WITHDRAWAL_AMOUNT=10.00
WITHDRAWAL_FEE_PERCENTAGE=2.5
```

For subscription prices, update in Stripe dashboard:
1. Products → Create product
2. Add pricing → Set monthly price
3. Copy price ID → Add to .env as `STRIPE_PRICE_ID_BASIC`, etc.

## 🧪 Testing Payments

Use Stripe test cards:

```
# Successful payment
Card: 4242 4242 4242 4242
Expiry: Any future date
CVC: Any 3 digits
ZIP: Any 5 digits

# Declined payment
Card: 4000 0000 0000 0002
```

## 🚨 Troubleshooting

### Payment fails with "No such payment_intent"
- Check Stripe API key is correct in .env
- Make sure you're using the right mode (test vs live)

### "Stripe library not available"
- Install: `pip install stripe==8.0.0`

### Smart contract deployment fails
- Check you have Sepolia ETH (get from faucet)
- Verify PRIVATE_KEY is set correctly
- Make sure RPC URL is working

### Webhook not receiving events
- In test mode, use Stripe CLI: `stripe listen --forward-to localhost:8000/api/v1/payments/webhook`
- In production, configure webhook in Stripe dashboard

## 📚 Next Steps

1. **Frontend Integration** - Add payment UI using Stripe.js
   - See [PAYMENT_SYSTEM.md](PAYMENT_SYSTEM.md) for frontend examples

2. **Enhanced Features** - Add more revenue streams
   - Verification API pricing
   - Tiered contribution fees
   - Premium features

3. **Scale** - Handle more traffic
   - Load balancing
   - Database optimization
   - Caching with Redis

4. **Marketing** - Get users and revenue
   - Launch campaign
   - Community building
   - Partnership outreach

## 💬 Support

- **Documentation:** See README.md, PAYMENT_SYSTEM.md, PRODUCTION_DEPLOYMENT.md
- **Issues:** https://github.com/Garrettc123/nwu-protocol/issues
- **Stripe Support:** https://support.stripe.com

## 🎉 You're Done!

Your NWU Protocol is now:
- ✅ Accepting payments
- ✅ Processing subscriptions
- ✅ Generating real revenue
- ✅ Ready to scale

**First month revenue target:** $1,000-$5,000
**First year revenue target:** $180,000+

Good luck! 🚀💰
