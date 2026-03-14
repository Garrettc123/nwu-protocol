# READY_TO_DEPLOY — NWU Protocol Production Checklist

This guide covers every step required to ship NWU Protocol to production with real-world currency processing (Stripe) and mainnet smart contract deployment.

---

## Pre-flight Checklist

Before deploying, confirm every item below is ✅.

### Environment & Secrets

- [ ] `STRIPE_SECRET_KEY` set to a live-mode `sk_live_...` key
- [ ] `STRIPE_PUBLISHABLE_KEY` set to a live-mode `pk_live_...` key
- [ ] `STRIPE_WEBHOOK_SECRET` set (from Stripe Dashboard → Webhooks → Signing Secret)
- [ ] `STRIPE_PRICE_ID_PRO` set (run `node scripts/setup-stripe-products.js` to create)
- [ ] `STRIPE_PRICE_ID_ENTERPRISE` set (same script)
- [ ] `JWT_SECRET_KEY` set to a strong random value (`python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `SECRET_KEY` set to a strong random value (same command)
- [ ] `DATABASE_URL` points to a production PostgreSQL instance (not localhost)
- [ ] `MONGO_URL` points to a production MongoDB instance
- [ ] `REDIS_URL` points to a production Redis instance
- [ ] `PRIVATE_KEY` (EVM deployer wallet) funded with enough ETH for gas
- [ ] `MAINNET_RPC_URL` set (e.g. Alchemy or Infura mainnet endpoint)
- [ ] `ETHERSCAN_API_KEY` set for contract verification
- [ ] All secrets stored in a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) — **never** committed to source control

### Stripe Product Setup

```bash
# Run once before going live
STRIPE_SECRET_KEY=sk_live_... node scripts/setup-stripe-products.js
```

Copy the printed `STRIPE_PRICE_ID_PRO` and `STRIPE_PRICE_ID_ENTERPRISE` values into your production environment.

### Smart Contract Deployment (Mainnet)

```bash
cd contracts

# 1. Install dependencies (includes dotenv)
npm install

# 2. Create .env from template — do NOT commit this file
cp .env.example .env
# Fill in: MAINNET_RPC_URL, PRIVATE_KEY, ETHERSCAN_API_KEY

# 3. Compile contracts
npm run compile

# 4. Run tests against a fork to validate before spending real ETH
npx hardhat test

# 5. Deploy to Ethereum mainnet
npm run deploy:mainnet

# 6. Verify contracts on Etherscan
npm run verify:mainnet
```

Deployed addresses are saved to `contracts/deployments/mainnet.json`.

### Backend Deployment

```bash
cd backend

# Install dependencies (includes stripe)
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server (production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use Docker Compose (recommended):

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Stripe Webhook Registration

1. In the Stripe Dashboard, go to **Developers → Webhooks → Add endpoint**.
2. Set the endpoint URL to `https://your-domain.com/api/v1/payments/webhook`.
3. Select these events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy the **Signing Secret** and set `STRIPE_WEBHOOK_SECRET` in your environment.

---

## Production Deployment Commands Reference

| Task                     | Command                                                     |
| ------------------------ | ----------------------------------------------------------- |
| Start all services       | `docker compose -f docker-compose.prod.yml up -d`           |
| Stop all services        | `docker compose -f docker-compose.prod.yml down`            |
| View logs                | `docker compose -f docker-compose.prod.yml logs -f backend` |
| Run DB migrations        | `docker compose exec backend alembic upgrade head`          |
| Deploy mainnet contracts | `cd contracts && npm run deploy:mainnet`                    |
| Verify on Etherscan      | `cd contracts && npm run verify:mainnet`                    |
| Set up Stripe products   | `node scripts/setup-stripe-products.js`                     |
| Health check             | `curl https://your-domain.com/health`                       |

---

## Post-Deployment Verification

Run through each of these after deploying to production:

- [ ] `GET /health` returns `"status": "healthy"` for all services
- [ ] `GET /api/v1/payments/pricing` returns all three tiers
- [ ] A test subscription can be created via the Stripe test-mode price ID
- [ ] Stripe webhook receives and processes a `payment_intent.succeeded` event
- [ ] JWT authentication works end-to-end (register → login → call protected endpoint)
- [ ] Smart contract addresses in `deployments/mainnet.json` are verified on Etherscan
- [ ] CORS is locked down to production frontend origin (not `*`)

---

## Security Reminders

- Rotate all secrets before going live if they were ever visible in logs or CI.
- Store `PRIVATE_KEY` in a hardware wallet or KMS for mainnet operations.
- Enable Stripe Radar rules to detect fraudulent payments.
- Set `allow_origins` in `backend/app/main.py` to your production domain only.
- Monitor Stripe Dashboard for failed payments and dispute activity.

---

## Revenue Streams

| Stream                  | Description                                     | Monthly Rate     |
| ----------------------- | ----------------------------------------------- | ---------------- |
| Pro Subscription        | 10K req/day, advanced verification              | $99/user         |
| Enterprise Subscription | 100K req/day, SLA, dedicated support            | $999/user        |
| Token Sales             | One-time NWU token purchases via payment intent | Variable         |
| API Usage Payouts       | Reward contributors for verified contributions  | Protocol-defined |

Pricing configuration lives in `backend/app/api/payments.py` (`/api/v1/payments/pricing`).  
To change prices, update both the Stripe Dashboard and the `price` field in that endpoint.
