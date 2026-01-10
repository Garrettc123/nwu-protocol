#!/usr/bin/env python3
"""
Setup script to create Stripe products and prices for NWU Protocol.
Run this after setting up your Stripe account to create subscription plans.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import stripe
except ImportError:
    print("❌ Stripe library not found. Install it with:")
    print("   pip install stripe")
    sys.exit(1)

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

if not stripe.api_key or not stripe.api_key.startswith("sk_"):
    print("❌ STRIPE_SECRET_KEY not found or invalid in .env file")
    print("Please add your Stripe secret key to .env:")
    print("   STRIPE_SECRET_KEY=sk_test_...")
    sys.exit(1)

print("🔧 NWU Protocol - Stripe Product Setup")
print("=" * 50)
print()

# Define products
products = [
    {
        "name": "Basic Plan",
        "description": "For individual developers - includes basic API access",
        "price": 4900,  # $49.00 in cents
        "key": "STRIPE_PRICE_ID_BASIC"
    },
    {
        "name": "Premium Plan",
        "description": "For small teams - includes advanced features and higher limits",
        "price": 14900,  # $149.00 in cents
        "key": "STRIPE_PRICE_ID_PREMIUM"
    },
    {
        "name": "Enterprise Plan",
        "description": "For large organizations - includes custom integrations and SLA",
        "price": 49900,  # $499.00 in cents
        "key": "STRIPE_PRICE_ID_ENTERPRISE"
    }
]

print("This script will create the following Stripe products:")
print()
for product in products:
    print(f"  • {product['name']}: ${product['price']/100:.2f}/month")
    print(f"    {product['description']}")
    print()

response = input("Continue? (y/n): ")
if response.lower() != 'y':
    print("Setup cancelled.")
    sys.exit(0)

print()
print("Creating products...")
print()

created_prices = []

for product_def in products:
    try:
        # Create product
        product = stripe.Product.create(
            name=product_def["name"],
            description=product_def["description"],
        )
        
        # Create price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=product_def["price"],
            currency="usd",
            recurring={"interval": "month"},
        )
        
        created_prices.append({
            "key": product_def["key"],
            "price_id": price.id,
            "product_name": product_def["name"]
        })
        
        print(f"✅ Created {product_def['name']}")
        print(f"   Product ID: {product.id}")
        print(f"   Price ID: {price.id}")
        print()
        
    except stripe.error.StripeError as e:
        print(f"❌ Error creating {product_def['name']}: {e}")
        print()

if created_prices:
    print()
    print("=" * 50)
    print("✅ Setup Complete!")
    print()
    print("Add these to your .env file:")
    print()
    for price in created_prices:
        print(f"{price['key']}={price['price_id']}")
    print()
    
    # Optionally update .env file
    update_env = input("Update .env file automatically? (y/n): ")
    if update_env.lower() == 'y':
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            # Update or add price IDs
            updated = False
            for i, line in enumerate(lines):
                for price in created_prices:
                    if line.startswith(price['key']):
                        lines[i] = f"{price['key']}={price['price_id']}\n"
                        updated = True
            
            # Add new lines if not found
            if not updated:
                for price in created_prices:
                    lines.append(f"{price['key']}={price['price_id']}\n")
            
            with open('.env', 'w') as f:
                f.writelines(lines)
            
            print()
            print("✅ .env file updated!")
            
        except Exception as e:
            print(f"❌ Error updating .env: {e}")
            print("Please add the price IDs manually.")
    
    print()
    print("🎉 Your Stripe products are ready!")
    print()
    print("Next steps:")
    print("  1. Test subscriptions with test card: 4242 4242 4242 4242")
    print("  2. Set up webhooks in Stripe dashboard")
    print("  3. Start accepting payments!")
    print()
else:
    print("⚠️  No products were created. Please check for errors above.")
