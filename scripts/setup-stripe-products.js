/**
 * Setup Stripe products and prices for NWU Protocol subscription tiers.
 *
 * Usage:
 *   STRIPE_SECRET_KEY=sk_live_... node scripts/setup-stripe-products.js
 *
 * Run once during initial Stripe configuration. Re-running is safe — it
 * checks for existing products/prices before creating new ones.
 */

const Stripe = require('stripe');

const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;
if (!STRIPE_SECRET_KEY) {
  console.error('Error: STRIPE_SECRET_KEY environment variable is required.');
  process.exit(1);
}

const stripe = new Stripe(STRIPE_SECRET_KEY, { apiVersion: '2023-10-16' });

const SUBSCRIPTION_TIERS = [
  {
    name: 'NWU Protocol Free',
    description: 'Free tier — 100 API requests/day, basic verification, community support.',
    tier: 'free',
    unitAmountUsd: 0,
    interval: 'month',
    metadata: { tier: 'free', rate_limit: '100' },
  },
  {
    name: 'NWU Protocol Pro',
    description:
      'Pro tier — 10,000 API requests/day, advanced verification, priority support, custom AI agents.',
    tier: 'pro',
    unitAmountUsd: 9900, // $99.00 in cents
    interval: 'month',
    metadata: { tier: 'pro', rate_limit: '10000' },
  },
  {
    name: 'NWU Protocol Enterprise',
    description:
      'Enterprise tier — 100,000 API requests/day, premium verification, 24/7 dedicated support, SLA guarantee.',
    tier: 'enterprise',
    unitAmountUsd: 99900, // $999.00 in cents
    interval: 'month',
    metadata: { tier: 'enterprise', rate_limit: '100000' },
  },
];

async function findExistingProduct(tierName) {
  const products = await stripe.products.list({ limit: 100 });
  return products.data.find(product => product.name === tierName && product.active) || null;
}

async function findExistingPrice(productId, unitAmount) {
  const prices = await stripe.prices.list({ product: productId, limit: 100 });
  return (
    prices.data.find(
      price => price.unit_amount === unitAmount && price.currency === 'usd' && price.active
    ) || null
  );
}

async function setupTier(tierConfig) {
  const { name, description, tier, unitAmountUsd, interval, metadata } = tierConfig;

  // Upsert product
  let product = await findExistingProduct(name);
  if (product) {
    console.log(`  Product already exists: ${product.id} (${name})`);
  } else {
    product = await stripe.products.create({
      name,
      description,
      metadata: { ...metadata, protocol: 'nwu' },
    });
    console.log(`  Created product: ${product.id} (${name})`);
  }

  // Free tier has no price
  if (unitAmountUsd === 0) {
    console.log(`  Skipping price creation for free tier.`);
    return { tier, productId: product.id, priceId: null };
  }

  // Upsert recurring price
  let price = await findExistingPrice(product.id, unitAmountUsd);
  if (price) {
    console.log(`  Price already exists: ${price.id} ($${unitAmountUsd / 100}/${interval})`);
  } else {
    price = await stripe.prices.create({
      product: product.id,
      unit_amount: unitAmountUsd,
      currency: 'usd',
      recurring: { interval },
      metadata,
    });
    console.log(`  Created price: ${price.id} ($${unitAmountUsd / 100}/${interval})`);
  }

  return { tier, productId: product.id, priceId: price.id };
}

async function main() {
  console.log('Setting up Stripe products and prices for NWU Protocol...\n');

  const results = [];
  for (const tierConfig of SUBSCRIPTION_TIERS) {
    console.log(`Processing tier: ${tierConfig.tier}`);
    const result = await setupTier(tierConfig);
    results.push(result);
    console.log('');
  }

  console.log('=== Stripe Setup Complete ===');
  console.log('Add the following price IDs to your backend .env / environment configuration:\n');
  for (const { tier, productId, priceId } of results) {
    const envKey = `STRIPE_PRICE_ID_${tier.toUpperCase()}`;
    console.log(`  ${envKey}=${priceId || 'N/A (free tier)'}`);
    console.log(`  Product: ${productId}`);
  }
  console.log(
    '\nAlso set STRIPE_SECRET_KEY (backend), STRIPE_PUBLISHABLE_KEY (frontend), and STRIPE_WEBHOOK_SECRET.'
  );
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
