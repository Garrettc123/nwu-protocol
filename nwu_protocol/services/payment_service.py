"""
Payment service for processing real-world currency transactions using Stripe.
"""

import os
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logging.warning("Stripe library not available. Payment processing disabled.")

logger = logging.getLogger(__name__)


class PaymentService:
    """Handle payment processing with Stripe."""
    
    def __init__(self):
        """Initialize payment service."""
        if STRIPE_AVAILABLE:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
            self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        else:
            logger.warning("Stripe not configured - payment features unavailable")
    
    def create_payment_intent(
        self, 
        amount: Decimal, 
        currency: str = "usd",
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent for processing payments.
        
        Args:
            amount: Amount in the currency's smallest unit (e.g., cents for USD)
            currency: Three-letter ISO currency code
            customer_email: Customer's email address
            metadata: Additional metadata to attach to the payment
            
        Returns:
            Payment intent object with client_secret for frontend
        """
        if not STRIPE_AVAILABLE:
            raise RuntimeError("Stripe not available")
        
        try:
            # Convert to cents/smallest currency unit
            amount_cents = int(amount * 100)
            
            intent_params = {
                "amount": amount_cents,
                "currency": currency,
                "automatic_payment_methods": {"enabled": True},
            }
            
            if customer_email:
                intent_params["receipt_email"] = customer_email
            
            if metadata:
                intent_params["metadata"] = metadata
            
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            logger.info(f"Payment intent created: {payment_intent.id}")
            
            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "amount": amount,
                "currency": currency,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            raise RuntimeError(f"Payment processing error: {str(e)}")
    
    def create_subscription(
        self,
        customer_email: str,
        price_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription for recurring payments.
        
        Args:
            customer_email: Customer's email address
            price_id: Stripe price ID for the subscription
            metadata: Additional metadata
            
        Returns:
            Subscription object
        """
        if not STRIPE_AVAILABLE:
            raise RuntimeError("Stripe not available")
        
        try:
            # Create or retrieve customer
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=customer_email)
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price_id}],
                metadata=metadata or {},
            )
            
            logger.info(f"Subscription created: {subscription.id}")
            
            return {
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise RuntimeError(f"Subscription error: {str(e)}")
    
    def create_payout(
        self,
        amount: Decimal,
        destination: str,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payout to transfer funds to a user's account.
        
        Args:
            amount: Amount to payout
            destination: Destination account (bank account or debit card)
            currency: Three-letter ISO currency code
            metadata: Additional metadata
            
        Returns:
            Payout object
        """
        if not STRIPE_AVAILABLE:
            raise RuntimeError("Stripe not available")
        
        try:
            amount_cents = int(amount * 100)
            
            payout = stripe.Payout.create(
                amount=amount_cents,
                currency=currency,
                destination=destination,
                metadata=metadata or {},
            )
            
            logger.info(f"Payout created: {payout.id}")
            
            return {
                "payout_id": payout.id,
                "amount": amount,
                "currency": currency,
                "status": payout.status,
                "arrival_date": payout.arrival_date,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payout: {str(e)}")
            raise RuntimeError(f"Payout error: {str(e)}")
    
    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verify and parse a Stripe webhook event.
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            
        Returns:
            Parsed webhook event
        """
        if not STRIPE_AVAILABLE:
            raise RuntimeError("Stripe not available")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except ValueError:
            raise RuntimeError("Invalid webhook payload")
        except stripe.error.SignatureVerificationError:
            raise RuntimeError("Invalid webhook signature")
    
    def calculate_token_price(
        self,
        token_amount: int,
        token_price_usd: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate USD price for a given number of tokens.
        
        Args:
            token_amount: Number of NWU tokens
            token_price_usd: Price per token in USD (defaults to env var)
            
        Returns:
            Total price in USD
        """
        if token_price_usd is None:
            token_price_usd = Decimal(os.getenv("NWU_TOKEN_PRICE_USD", "0.01"))
        
        return Decimal(token_amount) * token_price_usd
    
    def calculate_token_amount(
        self,
        usd_amount: Decimal,
        token_price_usd: Optional[Decimal] = None
    ) -> int:
        """
        Calculate number of tokens for a given USD amount.
        
        Args:
            usd_amount: Amount in USD
            token_price_usd: Price per token in USD (defaults to env var)
            
        Returns:
            Number of tokens
        """
        if token_price_usd is None:
            token_price_usd = Decimal(os.getenv("NWU_TOKEN_PRICE_USD", "0.01"))
        
        return int(usd_amount / token_price_usd)


# Singleton instance
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """Get the payment service instance."""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
