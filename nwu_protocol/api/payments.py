"""
Payment API endpoints for processing real-world currency transactions.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from decimal import Decimal
import logging

from nwu_protocol.services.payment_service import get_payment_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["payments"]
)


class PaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""
    amount: Decimal = Field(..., gt=0, description="Amount in USD")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email")
    token_amount: Optional[int] = Field(None, gt=0, description="Number of NWU tokens to purchase")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SubscriptionRequest(BaseModel):
    """Request to create a subscription."""
    customer_email: EmailStr
    plan: str = Field(..., description="Subscription plan: basic, premium, or enterprise")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PayoutRequest(BaseModel):
    """Request to create a payout."""
    amount: Decimal = Field(..., gt=0, description="Amount to payout in USD")
    destination: str = Field(..., description="Destination account ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TokenPriceRequest(BaseModel):
    """Request to calculate token price."""
    token_amount: int = Field(..., gt=0)


class TokenAmountRequest(BaseModel):
    """Request to calculate token amount."""
    usd_amount: Decimal = Field(..., gt=0)


@router.post("/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    """
    Create a payment intent for processing a one-time payment.
    
    This endpoint creates a Stripe payment intent that can be used
    on the frontend to collect payment details securely.
    """
    try:
        payment_service = get_payment_service()
        
        # If token_amount is provided, calculate the USD amount
        if request.token_amount:
            amount = payment_service.calculate_token_price(request.token_amount)
            request.metadata["token_amount"] = request.token_amount
        else:
            amount = request.amount
        
        result = payment_service.create_payment_intent(
            amount=amount,
            customer_email=request.customer_email,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-subscription")
async def create_subscription(request: SubscriptionRequest):
    """
    Create a recurring subscription.
    
    Available plans:
    - basic: For individual developers
    - premium: For small teams
    - enterprise: For large organizations
    """
    try:
        import os
        
        payment_service = get_payment_service()
        
        # Map plan to Stripe price ID
        plan_mapping = {
            "basic": os.getenv("STRIPE_PRICE_ID_BASIC"),
            "premium": os.getenv("STRIPE_PRICE_ID_PREMIUM"),
            "enterprise": os.getenv("STRIPE_PRICE_ID_ENTERPRISE"),
        }
        
        price_id = plan_mapping.get(request.plan.lower())
        if not price_id:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid plan: {request.plan}. Must be basic, premium, or enterprise"
            )
        
        result = payment_service.create_subscription(
            customer_email=request.customer_email,
            price_id=price_id,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-payout")
async def create_payout(request: PayoutRequest):
    """
    Create a payout to transfer funds to a user's account.
    
    This endpoint is used to pay out rewards to contributors in real currency.
    """
    try:
        import os
        
        # Check minimum withdrawal amount
        min_amount = Decimal(os.getenv("MIN_WITHDRAWAL_AMOUNT", "10.00"))
        if request.amount < min_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum withdrawal amount is ${min_amount}"
            )
        
        # Apply withdrawal fee
        fee_percentage = Decimal(os.getenv("WITHDRAWAL_FEE_PERCENTAGE", "2.5"))
        fee_amount = request.amount * (fee_percentage / 100)
        net_amount = request.amount - fee_amount
        
        payment_service = get_payment_service()
        
        request.metadata["gross_amount"] = str(request.amount)
        request.metadata["fee_amount"] = str(fee_amount)
        request.metadata["net_amount"] = str(net_amount)
        
        result = payment_service.create_payout(
            amount=net_amount,
            destination=request.destination,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "data": result,
            "fee_info": {
                "gross_amount": request.amount,
                "fee_percentage": fee_percentage,
                "fee_amount": fee_amount,
                "net_amount": net_amount
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payout: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle Stripe webhook events.
    
    This endpoint receives notifications about payment events
    such as successful payments, failed payments, and subscription changes.
    """
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        payment_service = get_payment_service()
        event = payment_service.verify_webhook(payload, signature)
        
        # Handle different event types
        event_type = event["type"]
        
        if event_type == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            logger.info(f"Payment succeeded: {payment_intent['id']}")
            # TODO: Update database, allocate tokens to user
            
        elif event_type == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            logger.warning(f"Payment failed: {payment_intent['id']}")
            # TODO: Notify user
            
        elif event_type == "customer.subscription.created":
            subscription = event["data"]["object"]
            logger.info(f"Subscription created: {subscription['id']}")
            # TODO: Update user subscription status
            
        elif event_type == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            logger.info(f"Subscription cancelled: {subscription['id']}")
            # TODO: Update user subscription status
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calculate-token-price")
async def calculate_token_price(request: TokenPriceRequest):
    """
    Calculate the USD price for a given number of NWU tokens.
    """
    try:
        payment_service = get_payment_service()
        price = payment_service.calculate_token_price(request.token_amount)
        
        return {
            "success": True,
            "data": {
                "token_amount": request.token_amount,
                "usd_price": float(price),
                "price_per_token": float(payment_service.calculate_token_price(1))
            }
        }
    except Exception as e:
        logger.error(f"Error calculating price: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-token-amount")
async def calculate_token_amount(request: TokenAmountRequest):
    """
    Calculate the number of NWU tokens for a given USD amount.
    """
    try:
        payment_service = get_payment_service()
        token_amount = payment_service.calculate_token_amount(request.usd_amount)
        
        return {
            "success": True,
            "data": {
                "usd_amount": float(request.usd_amount),
                "token_amount": token_amount,
                "price_per_token": float(payment_service.calculate_token_price(1))
            }
        }
    except Exception as e:
        logger.error(f"Error calculating tokens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_payment_config():
    """
    Get public payment configuration.
    
    Returns public keys and configuration needed by the frontend.
    """
    import os
    
    payment_service = get_payment_service()
    
    return {
        "success": True,
        "data": {
            "publishable_key": payment_service.publishable_key,
            "token_price_usd": os.getenv("NWU_TOKEN_PRICE_USD", "0.01"),
            "min_withdrawal_amount": os.getenv("MIN_WITHDRAWAL_AMOUNT", "10.00"),
            "withdrawal_fee_percentage": os.getenv("WITHDRAWAL_FEE_PERCENTAGE", "2.5"),
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
