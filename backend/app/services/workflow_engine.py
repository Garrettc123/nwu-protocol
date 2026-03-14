"""Progressive automation workflow engine for NWU Protocol.

This engine implements unprecedented harmoniously integrated automated business
turnkey automation with progressive capability levels.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from sqlalchemy.orm import Session
from ..models import Contribution, WorkflowExecution, EngagementHistory
import json


class WorkflowStage:
    """Workflow stage definition."""

    def __init__(
        self,
        name: str,
        automation_level: int,
        required_conditions: Optional[List[Callable]] = None,
        actions: Optional[List[Callable]] = None
    ):
        """Initialize workflow stage.

        Args:
            name: Stage name
            automation_level: Progressive automation level (0-5)
            required_conditions: List of condition functions to check
            actions: List of action functions to execute
        """
        self.name = name
        self.automation_level = automation_level
        self.required_conditions = required_conditions or []
        self.actions = actions or []


class ProgressiveAutomationEngine:
    """Progressive automation workflow engine.

    Implements 6 levels of progressive automation:
    Level 0: Manual processing only
    Level 1: Basic automated validation
    Level 2: Automated quality checks
    Level 3: Intelligent routing and prioritization
    Level 4: Predictive analysis and recommendations
    Level 5: Fully autonomous decision-making
    """

    def __init__(self, db: Session):
        """Initialize the automation engine.

        Args:
            db: Database session
        """
        self.db = db
        self.workflows: Dict[str, List[WorkflowStage]] = {}
        self._register_default_workflows()

    def _register_default_workflows(self):
        """Register default automation workflows."""
        # Contribution verification workflow
        self.register_workflow(
            "contribution_verification",
            [
                WorkflowStage("initial_validation", automation_level=1),
                WorkflowStage("quality_analysis", automation_level=2),
                WorkflowStage("intelligent_routing", automation_level=3),
                WorkflowStage("predictive_scoring", automation_level=4),
                WorkflowStage("autonomous_approval", automation_level=5)
            ]
        )

        # Engagement iteration workflow
        self.register_workflow(
            "engagement_iteration",
            [
                WorkflowStage("engagement_tracking", automation_level=1),
                WorkflowStage("pattern_analysis", automation_level=2),
                WorkflowStage("adaptive_response", automation_level=3),
                WorkflowStage("predictive_engagement", automation_level=4),
                WorkflowStage("autonomous_iteration", automation_level=5)
            ]
        )

        # Halt process automation workflow
        self.register_workflow(
            "halt_process_automation",
            [
                WorkflowStage("halt_detection", automation_level=1),
                WorkflowStage("automated_analysis", automation_level=2),
                WorkflowStage("intelligent_recovery", automation_level=3),
                WorkflowStage("predictive_prevention", automation_level=4),
                WorkflowStage("self_healing", automation_level=5)
            ]
        )

    def register_workflow(self, workflow_name: str, stages: List[WorkflowStage]):
        """Register a new workflow.

        Args:
            workflow_name: Name of the workflow
            stages: List of workflow stages
        """
        self.workflows[workflow_name] = stages

    def execute_workflow(
        self,
        contribution_id: int,
        workflow_name: str,
        max_automation_level: Optional[int] = None,
        workflow_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a progressive automation workflow.

        Args:
            contribution_id: ID of the contribution
            workflow_name: Name of the workflow to execute
            max_automation_level: Maximum automation level to apply (0-5)
            workflow_data: Optional workflow execution data

        Returns:
            WorkflowExecution object

        Raises:
            ValueError: If workflow not found or contribution not found
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")

        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Determine applicable automation level
        target_level = max_automation_level if max_automation_level is not None else 5
        target_level = min(target_level, contribution.automation_level + 1)  # Progressive increase

        # Find appropriate stage
        stages = self.workflows[workflow_name]
        applicable_stages = [s for s in stages if s.automation_level <= target_level]

        if not applicable_stages:
            applicable_stages = [stages[0]]  # At least execute first stage

        current_stage = applicable_stages[-1]  # Execute highest applicable stage

        # Create workflow execution record
        execution = WorkflowExecution(
            contribution_id=contribution_id,
            workflow_name=workflow_name,
            workflow_stage=current_stage.name,
            automation_level=current_stage.automation_level,
            execution_data=json.dumps(workflow_data or {}),
            status="running",
            started_at=datetime.utcnow()
        )
        self.db.add(execution)

        try:
            # Execute stage actions
            execution_result = self._execute_stage(
                contribution,
                current_stage,
                workflow_data or {}
            )

            # Update execution
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.execution_data = json.dumps({
                **(workflow_data or {}),
                "result": execution_result
            })

            # Update contribution automation level progressively
            if current_stage.automation_level > contribution.automation_level:
                contribution.automation_level = current_stage.automation_level

            contribution.process_stage = current_stage.name
            contribution.updated_at = datetime.utcnow()

            # Record engagement
            engagement = EngagementHistory(
                contribution_id=contribution_id,
                engagement_type="automation",
                engagement_data=json.dumps({
                    "workflow": workflow_name,
                    "stage": current_stage.name,
                    "automation_level": current_stage.automation_level,
                    "result": execution_result
                }),
                engagement_source="automation"
            )
            self.db.add(engagement)

            self.db.commit()
            self.db.refresh(execution)

            return execution

        except Exception as error:
            execution.status = "failed"
            execution.error_message = str(error)
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            raise

    def _execute_stage(
        self,
        contribution: Contribution,
        stage: WorkflowStage,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow stage.

        Args:
            contribution: Contribution object
            stage: WorkflowStage to execute
            workflow_data: Workflow execution data

        Returns:
            Stage execution result
        """
        result = {
            "stage": stage.name,
            "automation_level": stage.automation_level,
            "executed_at": datetime.utcnow().isoformat(),
            "conditions_met": True,
            "actions_executed": []
        }

        # Check conditions
        for condition in stage.required_conditions:
            if not condition(contribution, workflow_data):
                result["conditions_met"] = False
                result["failure_reason"] = f"Condition check failed in stage {stage.name}"
                return result

        # Execute actions
        for action in stage.actions:
            try:
                action_result = action(contribution, workflow_data)
                result["actions_executed"].append(action_result)
            except Exception as error:
                result["action_error"] = str(error)
                break

        return result

    def get_workflow_status(self, contribution_id: int) -> Dict[str, Any]:
        """Get workflow execution status for a contribution.

        Args:
            contribution_id: ID of the contribution

        Returns:
            Dictionary with workflow status
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        # Get recent workflow executions
        executions = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.contribution_id == contribution_id
        ).order_by(WorkflowExecution.created_at.desc()).limit(10).all()

        return {
            "contribution_id": contribution_id,
            "current_automation_level": contribution.automation_level,
            "current_process_stage": contribution.process_stage,
            "executions": [
                {
                    "workflow_name": exe.workflow_name,
                    "workflow_stage": exe.workflow_stage,
                    "automation_level": exe.automation_level,
                    "status": exe.status,
                    "started_at": exe.started_at.isoformat() if exe.started_at else None,
                    "completed_at": exe.completed_at.isoformat() if exe.completed_at else None,
                    "error_message": exe.error_message
                }
                for exe in executions
            ]
        }

    def advance_automation_level(
        self,
        contribution_id: int,
        target_level: Optional[int] = None
    ) -> Contribution:
        """Advance contribution to higher automation level.

        Args:
            contribution_id: ID of the contribution
            target_level: Target automation level (defaults to next level)

        Returns:
            Updated contribution
        """
        contribution = self.db.query(Contribution).filter(
            Contribution.id == contribution_id
        ).first()

        if not contribution:
            raise ValueError(f"Contribution {contribution_id} not found")

        current_level = contribution.automation_level
        new_level = target_level if target_level is not None else min(current_level + 1, 5)

        if new_level <= current_level:
            raise ValueError(f"Target level {new_level} must be higher than current level {current_level}")

        contribution.automation_level = new_level
        contribution.updated_at = datetime.utcnow()

        # Record engagement
        engagement = EngagementHistory(
            contribution_id=contribution_id,
            engagement_type="automation_advance",
            engagement_data=json.dumps({
                "previous_level": current_level,
                "new_level": new_level,
                "advanced_at": datetime.utcnow().isoformat()
            }),
            engagement_source="automation"
        )
        self.db.add(engagement)

        self.db.commit()
        self.db.refresh(contribution)

        return contribution
