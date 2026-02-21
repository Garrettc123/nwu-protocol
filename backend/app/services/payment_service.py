"""Payment service for Stripe integration."""

import stripe
import logging
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from ..config import settings
from ..models import Subscription, Payment, APIKey, SubscriptionTier, PaymentStatus, User
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.stripe_api_key:
    stripe.api_key = settings.stripe_api_key


class PaymentService:
    """Service for handling payment operations with Stripe."""
    
    def __init__(self):
        """Initialize payment service."""
        self.stripe_configured = bool(settings.stripe_api_key)
        if not self.stripe_configured:
            logger.warning("Stripe API key not configured. Payment features will be disabled.")
    
    async def create_customer(self, user: User, email: Optional[str] = None) -> Optional[str]:
        """
        Create a Stripe customer for a user.
        
        Args:
            user: User object
            email: Optional email address
            
        Returns:
            Stripe customer ID or None if failed
        """
        if not self.stripe_configured:
            logger.error("Stripe not configured")
            return None
        
        try:
            customer = stripe.Customer.create(
                email=email or user.email,
                metadata={
                    "user_id": user.id,
                    "address": user.address,
                    "username": user.username or ""
                }
            )
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None
    
    async def create_subscription(
        self,
        db: Session,
        user: User,
        tier: SubscriptionTier,
        stripe_price_id: str
    ) -> Optional[Subscription]:
        """
        Create a subscription for a user.
        
        Args:
            db: Database session
            user: User object
            tier: Subscription tier
            stripe_price_id: Stripe price ID
            
        Returns:
            Subscription object or None if failed
        """
        if not self.stripe_configured:
            logger.error("Stripe not configured")
            return None
        
        try:
            # Check if user has existing subscription
            existing_sub = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == "active"
            ).first()
            
            if existing_sub:
                logger.warning(f"User {user.id} already has an active subscription")
                return None
            
            # Get or create Stripe customer
            stripe_customer_id = None
            if hasattr(user, 'subscriptions') and user.subscriptions:
                for sub in user.subscriptions:
                    if sub.stripe_customer_id:
                        stripe_customer_id = sub.stripe_customer_id
                        break
            
            if not stripe_customer_id:
                stripe_customer_id = await self.create_customer(user)
                if not stripe_customer_id:
                    return None
            
            # Create Stripe subscription
            stripe_sub = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{"price": stripe_price_id}],
                metadata={
                    "user_id": user.id,
                    "tier": tier.value
                }
            )
            
            # Determine rate limit based on tier
            rate_limits = {
                SubscriptionTier.FREE: settings.subscription_tier_free_rate_limit,
                SubscriptionTier.PRO: settings.subscription_tier_pro_rate_limit,
                SubscriptionTier.ENTERPRISE: settings.subscription_tier_enterprise_rate_limit
            }
            
            # Generate API key
            api_key = self.generate_api_key()
            
            # Create subscription in database
            subscription = Subscription(
                user_id=user.id,
                tier=tier,
                stripe_subscription_id=stripe_sub.id,
                stripe_customer_id=stripe_customer_id,
                status=stripe_sub.status,
                current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end),
                api_key=api_key,
                rate_limit=rate_limits.get(tier, 100)
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"Created subscription {subscription.id} for user {user.id}")
            return subscription
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create subscription: {e}")
            return None
    
    async def cancel_subscription(
        self,
        db: Session,
        subscription_id: int,
        immediately: bool = False
    ) -> bool:
        """
        Cancel a subscription.
        
        Args:
            db: Database session
            subscription_id: Subscription ID
            immediately: If True, cancel immediately; otherwise at period end
            
        Returns:
            True if successful, False otherwise
        """
        if not self.stripe_configured:
            logger.error("Stripe not configured")
            return False
        
        try:
            subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return False
            
            if subscription.stripe_subscription_id:
                if immediately:
                    # Immediately cancel - use delete as last resort
                    try:
                        stripe.Subscription.modify(
                            subscription.stripe_subscription_id,
                            cancel_at_period_end=False
                        )
                        stripe.Subscription.delete(subscription.stripe_subscription_id)
                    except Exception as e:
                        logger.warning(f"Failed to delete subscription, marking as canceled: {e}")
                    subscription.status = "canceled"
                else:
                    # Cancel at period end (recommended approach)
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    subscription.cancel_at_period_end = True
                
                db.commit()
                logger.info(f"Canceled subscription {subscription_id}")
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    async def create_payment_intent(
        self,
        db: Session,
        user: User,
        amount: float,
        currency: str = "usd",
        description: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Stripe payment intent.
        
        Args:
            db: Database session
            user: User object
            amount: Amount in dollars
            currency: Currency code
            description: Payment description
            
        Returns:
            Payment intent details or None if failed
        """
        if not self.stripe_configured:
            logger.error("Stripe not configured")
            return None
        
        try:
            # Convert amount to cents
            amount_cents = int(amount * 100)
            
            # Get or create Stripe customer
            stripe_customer_id = None
            if hasattr(user, 'subscriptions') and user.subscriptions:
                for sub in user.subscriptions:
                    if sub.stripe_customer_id:
                        stripe_customer_id = sub.stripe_customer_id
                        break
            
            if not stripe_customer_id:
                stripe_customer_id = await self.create_customer(user)
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                customer=stripe_customer_id,
                description=description,
                metadata={
                    "user_id": user.id,
                    "address": user.address
                }
            )
            
            # Create payment record
            payment = Payment(
                user_id=user.id,
                stripe_payment_id=intent.id,
                amount=amount,
                currency=currency,
                status=PaymentStatus.PENDING,
                description=description
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            return {
                "payment_id": payment.id,
                "client_secret": intent.client_secret,
                "amount": amount,
                "currency": currency
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create payment intent: {e}")
            return None
    
    def generate_api_key(self) -> str:
        """
        Generate a secure API key.
        
        Returns:
            API key string
        """
        # Generate random key with prefix
        random_key = secrets.token_urlsafe(32)
        prefix = "nwu"
        return f"{prefix}_{random_key}"
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for storage.
        
        Args:
            api_key: API key to hash
            
        Returns:
            Hashed API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(
        self,
        db: Session,
        user: User,
        name: str,
        tier: SubscriptionTier
    ) -> Optional[Dict[str, Any]]:
        """
        Create an API key for a user.
        
        Args:
            db: Database session
            user: User object
            name: Key name/description
            tier: Subscription tier
            
        Returns:
            API key details or None if failed
        """
        try:
            # Generate API key
            api_key = self.generate_api_key()
            key_hash = self.hash_api_key(api_key)
            prefix = api_key[:12]  # Store first 12 chars for display
            
            # Set expiration (1 year from now)
            expires_at = datetime.utcnow() + timedelta(days=365)
            
            # Create API key record
            db_key = APIKey(
                user_id=user.id,
                key_hash=key_hash,
                name=name,
                prefix=prefix,
                tier=tier,
                expires_at=expires_at
            )
            
            db.add(db_key)
            db.commit()
            db.refresh(db_key)
            
            logger.info(f"Created API key {db_key.id} for user {user.id}")
            
            return {
                "id": db_key.id,
                "key": api_key,  # Return full key only once
                "prefix": prefix,
                "name": name,
                "tier": tier.value,
                "expires_at": expires_at.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create API key: {e}")
            return None
    
    async def verify_api_key(
        self,
        db: Session,
        api_key: str
    ) -> Optional[APIKey]:
        """
        Verify an API key.
        
        Args:
            db: Database session
            api_key: API key to verify
            
        Returns:
            APIKey object if valid, None otherwise
        """
        try:
            key_hash = self.hash_api_key(api_key)
            
            db_key = db.query(APIKey).filter(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            ).first()
            
            if not db_key:
                return None
            
            # Check expiration
            if db_key.expires_at and db_key.expires_at < datetime.utcnow():
                return None
            
            # Update last used timestamp
            db_key.last_used_at = datetime.utcnow()
            db.commit()
            
            return db_key
            
        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None
    
    async def handle_webhook(
        self,
        db: Session,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Handle Stripe webhook events.
        
        Args:
            db: Database session
            payload: Webhook payload
            signature: Stripe signature header
            
        Returns:
            True if handled successfully, False otherwise
        """
        if not self.stripe_configured or not settings.stripe_webhook_secret:
            logger.error("Stripe webhook not configured")
            return False
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
            
            # Handle different event types
            if event.type == "payment_intent.succeeded":
                await self._handle_payment_succeeded(db, event.data.object)
            elif event.type == "payment_intent.payment_failed":
                await self._handle_payment_failed(db, event.data.object)
            elif event.type == "customer.subscription.updated":
                await self._handle_subscription_updated(db, event.data.object)
            elif event.type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(db, event.data.object)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle webhook: {e}")
            return False
    
    async def _handle_payment_succeeded(self, db: Session, payment_intent: Any):
        """Handle successful payment."""
        payment = db.query(Payment).filter(
            Payment.stripe_payment_id == payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.SUCCEEDED
            db.commit()
            logger.info(f"Payment {payment.id} succeeded")
    
    async def _handle_payment_failed(self, db: Session, payment_intent: Any):
        """Handle failed payment."""
        payment = db.query(Payment).filter(
            Payment.stripe_payment_id == payment_intent.id
        ).first()
        
        if payment:
            payment.status = PaymentStatus.FAILED
            db.commit()
            logger.info(f"Payment {payment.id} failed")
    
    async def _handle_subscription_updated(self, db: Session, subscription: Any):
        """Handle subscription update."""
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription.id
        ).first()
        
        if sub:
            sub.status = subscription.status
            sub.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
            sub.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            db.commit()
            logger.info(f"Subscription {sub.id} updated")
    
    async def _handle_subscription_deleted(self, db: Session, subscription: Any):
        """Handle subscription deletion."""
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription.id
        ).first()
        
        if sub:
            sub.status = "canceled"
            db.commit()
            logger.info(f"Subscription {sub.id} canceled")


# Global payment service instance
payment_service = PaymentService()
