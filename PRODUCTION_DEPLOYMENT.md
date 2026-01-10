# Production Deployment Guide for NWU Protocol

## Prerequisites

Before deploying to production and enabling real-world currency generation, ensure you have:

1. **API Keys & Credentials**
   - Stripe account (for payment processing)
   - OpenAI API key (for AI verification)
   - Ethereum mainnet RPC URL (Infura/Alchemy)
   - Private key for contract deployment
   - Etherscan API key for contract verification

2. **Infrastructure**
   - Production server or cloud hosting (AWS, GCP, Azure, or Vercel)
   - PostgreSQL database
   - Redis instance
   - MongoDB instance
   - RabbitMQ message queue
   - IPFS node or Pinata/Infura IPFS service

3. **Security**
   - SSL certificate for HTTPS
   - Environment variables properly configured
   - Firewall rules configured
   - Rate limiting enabled

## Step 1: Environment Configuration

Create a `.env` file with production values:

```bash
# Database
MONGODB_URI=mongodb://[production-mongodb-url]
DATABASE_URL=postgresql://[production-postgres-url]
REDIS_URL=redis://[production-redis-url]

# IPFS
IPFS_API_URL=https://ipfs.infura.io:5001
IPFS_GATEWAY_URL=https://gateway.pinata.cloud

# API Keys
OPENAI_API_KEY=sk-[your-openai-key]

# Blockchain - MAINNET
ETHEREUM_MAINNET_RPC_URL=https://mainnet.infura.io/v3/[YOUR_PROJECT_ID]
PRIVATE_KEY=[your-private-key-for-deployment]
ETHERSCAN_API_KEY=[your-etherscan-key]

# Payment Processing - PRODUCTION KEYS
STRIPE_SECRET_KEY=sk_live_[your-live-key]
STRIPE_PUBLISHABLE_KEY=pk_live_[your-live-key]
STRIPE_WEBHOOK_SECRET=whsec_[your-webhook-secret]
STRIPE_PRICE_ID_BASIC=price_[basic-plan-id]
STRIPE_PRICE_ID_PREMIUM=price_[premium-plan-id]
STRIPE_PRICE_ID_ENTERPRISE=price_[enterprise-plan-id]

# Token Economics
NWU_TOKEN_PRICE_USD=0.01
MIN_WITHDRAWAL_AMOUNT=10.00
WITHDRAWAL_FEE_PERCENTAGE=2.5

# Environment
NODE_ENV=production
DEBUG=false

# Ports
API_PORT=8000
```

## Step 2: Deploy Smart Contracts to Mainnet

**⚠️ WARNING: Deploying to mainnet requires real ETH for gas fees**

1. **Test on Sepolia first:**
   ```bash
   cd contracts
   npm install
   npx hardhat compile
   npx hardhat test
   npx hardhat run scripts/deploy.js --network sepolia
   ```

2. **Verify everything works on testnet, then deploy to mainnet:**
   ```bash
   npx hardhat run scripts/deploy.js --network mainnet
   ```

3. **Verify contracts on Etherscan:**
   ```bash
   npx hardhat verify --network mainnet [CONTRACT_ADDRESS]
   ```

4. **Save contract addresses** - Update your .env file:
   ```bash
   NWU_TOKEN_ADDRESS=0x...
   VERIFICATION_REGISTRY_ADDRESS=0x...
   REWARD_DISTRIBUTION_ADDRESS=0x...
   ```

## Step 3: Set Up Stripe

1. **Create Stripe Account** at https://stripe.com

2. **Create Products and Prices:**
   - Go to Products in Stripe Dashboard
   - Create three products:
     - Basic Plan ($49/month)
     - Premium Plan ($149/month)
     - Enterprise Plan ($499/month)
   - Copy the Price IDs to your .env file

3. **Set Up Webhook:**
   - Go to Developers > Webhooks
   - Add endpoint: `https://your-domain.com/api/v1/payments/webhook`
   - Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`, `customer.subscription.*`
   - Copy webhook signing secret to .env

4. **Enable Payouts:**
   - Complete Stripe verification
   - Add bank account for receiving payments
   - Enable Connect for payouts to contributors

## Step 4: Deploy Backend API

### Option A: Docker Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

### Option B: Vercel Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod

# Set environment variables in Vercel dashboard
```

### Option C: Traditional Server Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (if applicable)
python -m alembic upgrade head

# Start with gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Step 5: Deploy Frontend (Optional)

```bash
cd frontend
npm install
npm run build

# Deploy to Vercel, Netlify, or your hosting provider
vercel --prod
```

## Step 6: Test Payment Flow

1. **Test Payment Intent Creation:**
   ```bash
   curl -X POST https://your-domain.com/api/v1/payments/create-payment-intent \
     -H "Content-Type: application/json" \
     -d '{
       "amount": 10.00,
       "customer_email": "test@example.com"
     }'
   ```

2. **Test Token Price Calculation:**
   ```bash
   curl -X POST https://your-domain.com/api/v1/payments/calculate-token-price \
     -H "Content-Type: application/json" \
     -d '{"token_amount": 1000}'
   ```

3. **Test Webhook Delivery:**
   - Use Stripe CLI: `stripe listen --forward-to localhost:8000/api/v1/payments/webhook`
   - Or test in Stripe dashboard

## Step 7: Enable Real Currency Generation

### Revenue Streams

1. **Token Sales:**
   - Users purchase NWU tokens via Stripe
   - Tokens are minted and sent to their wallets
   - Revenue: $0.01 per token sold

2. **Subscription Plans:**
   - Basic: $49/month - Individual developers
   - Premium: $149/month - Small teams  
   - Enterprise: $499/month - Large organizations
   - Revenue: Recurring monthly income

3. **Transaction Fees:**
   - 2.5% fee on all withdrawals
   - Revenue: Percentage of all payouts

4. **Verification Services:**
   - Charge enterprises for verification API access
   - Revenue: Pay-per-verification model

### Monitoring Revenue

Track key metrics:
- Total payment volume
- Active subscriptions
- Token sales
- Withdrawal requests
- Revenue by source

## Step 8: Security Checklist

- [ ] SSL/HTTPS enabled
- [ ] API rate limiting configured
- [ ] CORS properly configured
- [ ] Database backups automated
- [ ] Secrets stored securely (not in code)
- [ ] Webhook signatures verified
- [ ] Input validation on all endpoints
- [ ] Error messages don't leak sensitive info
- [ ] Smart contracts audited
- [ ] Monitoring and alerting setup

## Step 9: Legal & Compliance

- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] Cookie policy (if applicable)
- [ ] GDPR compliance (if serving EU)
- [ ] Payment processor agreement accepted
- [ ] Tax reporting setup
- [ ] Business entity registered
- [ ] Cryptocurrency regulations reviewed

## Step 10: Go Live

1. **Soft Launch:**
   - Enable for beta users only
   - Test all payment flows
   - Monitor for errors

2. **Full Launch:**
   - Open to public
   - Marketing campaign
   - Community announcement

3. **Monitor:**
   - Check error logs daily
   - Monitor payment success rate
   - Track user feedback
   - Watch for security issues

## Maintenance

### Daily Tasks
- Check error logs
- Monitor payment processing
- Review user feedback

### Weekly Tasks
- Review revenue metrics
- Check system performance
- Update dependencies (security patches)

### Monthly Tasks
- Smart contract balance check
- Security audit
- Backup verification
- Performance optimization

## Support & Troubleshooting

### Common Issues

1. **Payment fails:**
   - Check Stripe API keys
   - Verify webhook secret
   - Check customer card details

2. **Smart contract interaction fails:**
   - Verify contract addresses
   - Check gas prices
   - Ensure wallet has ETH for gas

3. **Tokens not minting:**
   - Check minter permissions
   - Verify contract not paused
   - Check max supply limit

### Getting Help

- GitHub Issues: https://github.com/Garrettc123/nwu-protocol/issues
- Documentation: See README.md
- Email: support@nwu-protocol.com (update with your email)

## Revenue Projections

Based on the monetization strategy:

**Year 1 Target:**
- 1,000 token buyers/month: $10,000/month
- 50 basic subscriptions: $2,450/month
- 10 premium subscriptions: $1,490/month
- 2 enterprise subscriptions: $998/month
- Transaction fees: ~$500/month

**Total Monthly Revenue (Year 1):** ~$15,000/month
**Total Annual Revenue (Year 1):** ~$180,000/year

## Conclusion

Your NWU Protocol is now deployed and generating real-world currency! 

Remember to:
- Keep security as top priority
- Monitor systems constantly
- Respond to user feedback
- Scale infrastructure as needed
- Comply with all regulations

Good luck! 🚀
