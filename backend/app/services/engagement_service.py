"""Engagement iteration tracking system for NWU Protocol.

Tracks user engagement patterns and manages iterative contribution refinement.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models import (
    Contribution,
    EngagementHistory,
    ProcessIteration,
    User
)
import json


class EngagementIterationService:
    """Service for tracking and managing engagement iterations."""

    # Engagement type weights for scoring
    ENGAGEMENT_WEIGHTS = {
        "view": 0.5,
        "comment": 2.0,
        "share": 3.0,
        "iterate": 5.0,
        "halt": 1.0,
        "resume": 2.5,
        "halt_approval": 4.0,
        "automation": 1.5,
        "automation_advance": 3.0
    }

    def __init__(self, db: Session):
        """Initialize the engagement iteration service.

        Args:
            db: Database session
        """
        self.db = db

    def record_engagement(
        self,
        contribution_id: int,
        engagement_type: str,
        user_id: Optional[int] = None,
        engagement_data: Optional[Dict[str, Any]] = None,
        source: str = "api"
    ) -> EngagementHistory:
        """Record an engagement event.

        Args:
            contribution_id: ID of the contribution
            engagement_type: Type of engagement
            user_id: Optional user ID
            engagement_data: Optional engagement data
            source: Engagement source (web, api, automation)

        Returns:
            EngagementHistory object
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Create engagement record
        engagement = EngagementHistory(
            contribution_id=contribution_id,
            user_id=user_id,
            engagement_type=engagement_type,
            engagement_data=json.dumps(engagement_data or {}),
            engagement_source=source
        )
        self.db.add(engagement)

        # Update contribution metrics
        contribution.engagement_count += 1
        engagement_weight = self.ENGAGEMENT_WEIGHTS.get(engagement_type, 1.0)
        contribution.engagement_score += engagement_weight
        contribution.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(engagement)

        return engagement

    def create_iteration(
        self,
        contribution_id: int,
        previous_status: str,
        new_status: str,
        iteration_type: str,
        reason: str,
        changes: Optional[Dict[str, Any]] = None,
        quality_delta: Optional[float] = None
    ) -> ProcessIteration:
        """Create a new process iteration.

        Args:
            contribution_id: ID of the contribution
            previous_status: Previous contribution status
            new_status: New contribution status
            iteration_type: Type of iteration (automatic, manual, triggered)
            reason: Reason for iteration
            changes: Optional dictionary of changes
            quality_delta: Optional change in quality score

        Returns:
            ProcessIteration object
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Create iteration record
        iteration = ProcessIteration(
            contribution_id=contribution_id,
            iteration_number=contribution.iteration_count + 1,
            previous_status=previous_status,
            new_status=new_status,
            iteration_type=iteration_type,
            iteration_reason=reason,
            changes_summary=json.dumps(changes or {}),
            quality_delta=quality_delta
        )
        self.db.add(iteration)

        # Update contribution
        contribution.iteration_count += 1
        contribution.status = new_status
        contribution.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(iteration)

        return iteration

    def get_engagement_analytics(
        self,
        contribution_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get engagement analytics for a contribution.

        Args:
            contribution_id: ID of the contribution
            days: Number of days to analyze

        Returns:
            Dictionary with engagement analytics
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Calculate date threshold
        threshold = datetime.utcnow() - timedelta(days=days)

        # Get engagements
        engagements = self.db.query(EngagementHistory).filter(
            EngagementHistory.contribution_id == contribution_id,
            EngagementHistory.created_at >= threshold
        ).all()

        # Analyze by type
        type_counts = {}
        for engagement in engagements:
            type_counts[engagement.engagement_type] = type_counts.get(
                engagement.engagement_type, 0
            ) + 1

        # Analyze by source
        source_counts = {}
        for engagement in engagements:
            source_counts[engagement.engagement_source] = source_counts.get(
                engagement.engagement_source, 0
            ) + 1

        # Calculate engagement velocity (engagements per day)
        velocity = len(engagements) / days if days > 0 else 0

        # Get unique users
        unique_users = len(set(
            e.user_id for e in engagements if e.user_id is not None
        ))

        return {
            "contribution_id": contribution_id,
            "total_engagement_count": contribution.engagement_count,
            "engagement_score": contribution.engagement_score,
            "period_days": days,
            "recent_engagements": len(engagements),
            "engagement_velocity": round(velocity, 2),
            "unique_users": unique_users,
            "engagement_by_type": type_counts,
            "engagement_by_source": source_counts,
            "iteration_count": contribution.iteration_count
        }

    def get_iteration_history(
        self,
        contribution_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get iteration history for a contribution.

        Args:
            contribution_id: ID of the contribution
            limit: Maximum number of iterations to return

        Returns:
            List of iteration dictionaries
        """
        iterations = self.db.query(ProcessIteration).filter(
            ProcessIteration.contribution_id == contribution_id
        ).order_by(ProcessIteration.created_at.desc()).limit(limit).all()

        return [
            {
                "iteration_number": iteration.iteration_number,
                "previous_status": iteration.previous_status,
                "new_status": iteration.new_status,
                "iteration_type": iteration.iteration_type,
                "reason": iteration.iteration_reason,
                "changes": json.loads(iteration.changes_summary) if iteration.changes_summary else None,
                "quality_delta": iteration.quality_delta,
                "created_at": iteration.created_at.isoformat()
            }
            for iteration in iterations
        ]

    def calculate_engagement_trends(
        self,
        contribution_id: int
    ) -> Dict[str, Any]:
        """Calculate engagement trends and patterns.

        Args:
            contribution_id: ID of the contribution

        Returns:
            Dictionary with trend analysis
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Get engagements for last 7 and 30 days
        now = datetime.utcnow()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        recent_engagements = self.db.query(EngagementHistory).filter(
            EngagementHistory.contribution_id == contribution_id,
            EngagementHistory.created_at >= last_7_days
        ).count()

        monthly_engagements = self.db.query(EngagementHistory).filter(
            EngagementHistory.contribution_id == contribution_id,
            EngagementHistory.created_at >= last_30_days
        ).count()

        # Calculate trends
        weekly_velocity = recent_engagements / 7
        monthly_velocity = monthly_engagements / 30

        # Determine trend direction
        if weekly_velocity > monthly_velocity * 1.2:
            trend = "increasing"
        elif weekly_velocity < monthly_velocity * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"

        # Get recent iterations
        recent_iterations = self.db.query(ProcessIteration).filter(
            ProcessIteration.contribution_id == contribution_id,
            ProcessIteration.created_at >= last_30_days
        ).count()

        return {
            "contribution_id": contribution_id,
            "trend": trend,
            "weekly_engagements": recent_engagements,
            "monthly_engagements": monthly_engagements,
            "weekly_velocity": round(weekly_velocity, 2),
            "monthly_velocity": round(monthly_velocity, 2),
            "recent_iterations": recent_iterations,
            "engagement_score": contribution.engagement_score,
            "health_status": self._calculate_health_status(
                contribution,
                weekly_velocity,
                recent_iterations
            )
        }

    def _calculate_health_status(
        self,
        contribution: Contribution,
        velocity: float,
        iterations: int
    ) -> str:
        """Calculate contribution health status.

        Args:
            contribution: Contribution object
            velocity: Engagement velocity
            iterations: Recent iteration count

        Returns:
            Health status string
        """
        # Calculate health based on multiple factors
        if contribution.halt_status == "halted":
            return "halted"

        if velocity >= 2.0 and iterations >= 2:
            return "healthy"
        elif velocity >= 1.0 or iterations >= 1:
            return "moderate"
        elif velocity >= 0.5:
            return "low_activity"
        else:
            return "inactive"

    def get_user_engagement_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get engagement summary for a user.

        Args:
            user_id: ID of the user
            days: Number of days to analyze

        Returns:
            Dictionary with user engagement summary
        """
        threshold = datetime.utcnow() - timedelta(days=days)

        # Get user engagements
        engagements = self.db.query(EngagementHistory).filter(
            EngagementHistory.user_id == user_id,
            EngagementHistory.created_at >= threshold
        ).all()

        # Count contributions engaged with
        contribution_ids = set(e.contribution_id for e in engagements)

        # Analyze by type
        type_counts = {}
        for engagement in engagements:
            type_counts[engagement.engagement_type] = type_counts.get(
                engagement.engagement_type, 0
            ) + 1

        return {
            "user_id": user_id,
            "period_days": days,
            "total_engagements": len(engagements),
            "contributions_engaged": len(contribution_ids),
            "engagement_by_type": type_counts,
            "average_daily_engagements": round(len(engagements) / days, 2)
        }
