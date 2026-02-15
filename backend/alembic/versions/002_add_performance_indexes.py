"""Add performance indexes

Revision ID: 002
Revises: 001
Create Date: 2026-02-15 19:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add indexes for foreign keys to improve join performance
    op.create_index(op.f('ix_contributions_user_id'), 'contributions', ['user_id'], unique=False)
    op.create_index(op.f('ix_contributions_status'), 'contributions', ['status'], unique=False)
    
    op.create_index(op.f('ix_verifications_contribution_id'), 'verifications', ['contribution_id'], unique=False)
    
    op.create_index(op.f('ix_rewards_user_id'), 'rewards', ['user_id'], unique=False)
    op.create_index(op.f('ix_rewards_contribution_id'), 'rewards', ['contribution_id'], unique=False)
    op.create_index(op.f('ix_rewards_status'), 'rewards', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rewards_status'), table_name='rewards')
    op.drop_index(op.f('ix_rewards_contribution_id'), table_name='rewards')
    op.drop_index(op.f('ix_rewards_user_id'), table_name='rewards')
    
    op.drop_index(op.f('ix_verifications_contribution_id'), table_name='verifications')
    
    op.drop_index(op.f('ix_contributions_status'), table_name='contributions')
    op.drop_index(op.f('ix_contributions_user_id'), table_name='contributions')
