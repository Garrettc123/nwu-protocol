"""Halt process management service for NWU Protocol."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import Contribution, EngagementHistory, ProcessIteration
import json


class HaltProcessService:
    """Service for managing halt, pause, and resume operations on contributions."""

    def __init__(self, db: Session):
        """Initialize the halt process service.

        Args:
            db: Database session
        """
        self.db = db

    def halt_contribution(
        self,
        contribution_id: int,
        reason: str,
        user_id: Optional[int] = None,
        halt_data: Optional[Dict[str, Any]] = None
    ) -> Contribution:
        """Halt a contribution process.

        Args:
            contribution_id: ID of the contribution to halt
            reason: Reason for halting
            user_id: Optional user ID who initiated the halt
            halt_data: Optional additional halt data

        Returns:
            Updated contribution object

        Raises:
            ValueError: If contribution not found or already halted
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        if contribution.halt_status == "halted":
            raise ValueError(f"Contribution {contribution_id} is already halted")

        # Store previous status for iteration tracking
        previous_status = contribution.status

        # Update contribution
        contribution.halt_status = "halted"
        contribution.halt_reason = reason
        contribution.halted_at = datetime.utcnow()
        contribution.status = "halted"
        contribution.updated_at = datetime.utcnow()

        # Record engagement
        engagement = EngagementHistory(
            contribution_id=contribution_id,
            user_id=user_id,
            engagement_type="halt",
            engagement_data=json.dumps({
                "reason": reason,
                "previous_status": previous_status,
                "halt_data": halt_data or {}
            }),
            engagement_source="api"
        )
        self.db.add(engagement)

        # Record iteration
        iteration = ProcessIteration(
            contribution_id=contribution_id,
            iteration_number=contribution.iteration_count + 1,
            previous_status=previous_status,
            new_status="halted",
            iteration_type="manual",
            iteration_reason=reason,
            changes_summary=json.dumps({
                "action": "halt",
                "reason": reason
            })
        )
        self.db.add(iteration)
        contribution.iteration_count += 1

        self.db.commit()
        self.db.refresh(contribution)

        return contribution

    def pause_contribution(
        self,
        contribution_id: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> Contribution:
        """Pause a contribution process temporarily.

        Args:
            contribution_id: ID of the contribution to pause
            reason: Reason for pausing
            user_id: Optional user ID who initiated the pause

        Returns:
            Updated contribution object
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        previous_status = contribution.status

        contribution.halt_status = "paused"
        contribution.halt_reason = reason
        contribution.halted_at = datetime.utcnow()
        contribution.status = "paused"
        contribution.updated_at = datetime.utcnow()

        # Record engagement
        engagement = EngagementHistory(
            contribution_id=contribution_id,
            user_id=user_id,
            engagement_type="pause",
            engagement_data=json.dumps({
                "reason": reason,
                "previous_status": previous_status
            }),
            engagement_source="api"
        )
        self.db.add(engagement)

        self.db.commit()
        self.db.refresh(contribution)

        return contribution

    def resume_contribution(
        self,
        contribution_id: int,
        user_id: Optional[int] = None,
        resume_to_status: Optional[str] = None
    ) -> Contribution:
        """Resume a halted or paused contribution.

        Args:
            contribution_id: ID of the contribution to resume
            user_id: Optional user ID who initiated the resume
            resume_to_status: Optional status to resume to (defaults to verifying)

        Returns:
            Updated contribution object
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        if contribution.halt_status not in ["halted", "paused"]:
            raise ValueError(f"Contribution {contribution_id} is not halted or paused")

        previous_halt_status = contribution.halt_status
        previous_status = contribution.status

        # Determine target status
        target_status = resume_to_status or "verifying"

        # Update contribution
        contribution.halt_status = "resumed"
        contribution.resumed_at = datetime.utcnow()
        contribution.status = target_status
        contribution.updated_at = datetime.utcnow()

        # Record engagement
        engagement = EngagementHistory(
            contribution_id=contribution_id,
            user_id=user_id,
            engagement_type="resume",
            engagement_data=json.dumps({
                "previous_halt_status": previous_halt_status,
                "previous_status": previous_status,
                "resumed_to_status": target_status,
                "halt_reason": contribution.halt_reason
            }),
            engagement_source="api"
        )
        self.db.add(engagement)

        # Record iteration
        iteration = ProcessIteration(
            contribution_id=contribution_id,
            iteration_number=contribution.iteration_count + 1,
            previous_status=previous_status,
            new_status=target_status,
            iteration_type="manual",
            iteration_reason="Resumed from halt/pause",
            changes_summary=json.dumps({
                "action": "resume",
                "from_halt_status": previous_halt_status,
                "to_status": target_status
            })
        )
        self.db.add(iteration)
        contribution.iteration_count += 1

        # Clear halt reason after recording
        contribution.halt_reason = None

        self.db.commit()
        self.db.refresh(contribution)

        return contribution

    def get_halt_status(self, contribution_id: int) -> Dict[str, Any]:
        """Get detailed halt status information.

        Args:
            contribution_id: ID of the contribution

        Returns:
            Dictionary with halt status details
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Get recent halt/resume engagements
        halt_engagements = self.db.query(EngagementHistory).filter(
            EngagementHistory.contribution_id == contribution_id,
            EngagementHistory.engagement_type.in_(["halt", "pause", "resume"])
        ).order_by(EngagementHistory.created_at.desc()).limit(5).all()

        return {
            "contribution_id": contribution_id,
            "current_status": contribution.status,
            "halt_status": contribution.halt_status,
            "halt_reason": contribution.halt_reason,
            "halted_at": contribution.halted_at.isoformat() if contribution.halted_at else None,
            "resumed_at": contribution.resumed_at.isoformat() if contribution.resumed_at else None,
            "iteration_count": contribution.iteration_count,
            "recent_engagements": [
                {
                    "type": eng.engagement_type,
                    "created_at": eng.created_at.isoformat(),
                    "data": json.loads(eng.engagement_data) if eng.engagement_data else None
                }
                for eng in halt_engagements
            ]
        }

    def approve_halt_engagement(
        self,
        contribution_id: int,
        approval_reason: str,
        user_id: Optional[int] = None
    ) -> Contribution:
        """Approve any halt process by engaging with iteration.

        This method implements the core requirement: "Approve any halt process
        by engaging and iteration". It allows progressive engagement with halted
        processes and manages their iteration cycles.

        Args:
            contribution_id: ID of the contribution
            approval_reason: Reason for approval
            user_id: Optional user ID approving the halt

        Returns:
            Updated contribution object
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Record approval engagement
        engagement = EngagementHistory(
            contribution_id=contribution_id,
            user_id=user_id,
            engagement_type="halt_approval",
            engagement_data=json.dumps({
                "approval_reason": approval_reason,
                "current_halt_status": contribution.halt_status,
                "current_status": contribution.status,
                "approved_at": datetime.utcnow().isoformat()
            }),
            engagement_source="api"
        )
        self.db.add(engagement)

        # Increment engagement metrics
        contribution.engagement_count += 1
        contribution.engagement_score += 1.0  # Each approval adds to engagement score

        self.db.commit()
        self.db.refresh(contribution)

        return contribution
