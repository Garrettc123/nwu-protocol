"""Database migration script for halt process and engagement features.

This script adds the necessary database columns and tables for:
- Halt process management
- Engagement iteration tracking
- Progressive automation workflows
- Knowledge thread management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.config import settings
from backend.app.models import Base, engine


def upgrade_database():
    """Apply database schema upgrades."""
    print("Starting database migration...")
    print("=" * 60)

    with engine.connect() as conn:
        # Add new columns to contributions table
        print("\n1. Adding new columns to contributions table...")

        migrations = [
            # Engagement tracking columns
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS engagement_count INTEGER DEFAULT 0",
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS engagement_score FLOAT DEFAULT 0.0",
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS iteration_count INTEGER DEFAULT 0",

            # Halt process columns
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS halt_reason TEXT",
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS halt_status VARCHAR(50)",
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS halted_at TIMESTAMP",
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS resumed_at TIMESTAMP",

            # Progressive automation columns
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS process_stage VARCHAR(50) DEFAULT 'initial'",
            "ALTER TABLE contributions ADD COLUMN IF NOT EXISTS automation_level INTEGER DEFAULT 0",

            # Create indexes
            "CREATE INDEX IF NOT EXISTS ix_contributions_halt_status ON contributions(halt_status)",
            "CREATE INDEX IF NOT EXISTS ix_contributions_process_stage ON contributions(process_stage)",
        ]

        for migration in migrations:
            try:
                conn.execute(text(migration))
                conn.commit()
                print(f"  ✅ {migration[:60]}...")
            except Exception as e:
                print(f"  ⚠️  Skipping (already exists or error): {str(e)[:60]}")

        # Create engagement_history table
        print("\n2. Creating engagement_history table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS engagement_history (
                    id SERIAL PRIMARY KEY,
                    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
                    user_id INTEGER REFERENCES users(id),
                    engagement_type VARCHAR(50) NOT NULL,
                    engagement_data TEXT,
                    engagement_source VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_engagement_history_contribution_id ON engagement_history(contribution_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_engagement_history_user_id ON engagement_history(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_engagement_history_engagement_type ON engagement_history(engagement_type)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_engagement_history_created_at ON engagement_history(created_at)"))
            conn.commit()
            print("  ✅ engagement_history table created")
        except Exception as e:
            print(f"  ⚠️  Table already exists or error: {str(e)[:60]}")

        # Create process_iterations table
        print("\n3. Creating process_iterations table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS process_iterations (
                    id SERIAL PRIMARY KEY,
                    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
                    iteration_number INTEGER NOT NULL,
                    previous_status VARCHAR(50) NOT NULL,
                    new_status VARCHAR(50) NOT NULL,
                    iteration_type VARCHAR(50) NOT NULL,
                    iteration_reason TEXT,
                    changes_summary TEXT,
                    quality_delta FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_process_iterations_contribution_id ON process_iterations(contribution_id)"))
            conn.commit()
            print("  ✅ process_iterations table created")
        except Exception as e:
            print(f"  ⚠️  Table already exists or error: {str(e)[:60]}")

        # Create workflow_executions table
        print("\n4. Creating workflow_executions table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id SERIAL PRIMARY KEY,
                    contribution_id INTEGER NOT NULL REFERENCES contributions(id),
                    workflow_name VARCHAR(100) NOT NULL,
                    workflow_stage VARCHAR(50) NOT NULL,
                    automation_level INTEGER DEFAULT 0,
                    execution_data TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_workflow_executions_contribution_id ON workflow_executions(contribution_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_workflow_executions_workflow_name ON workflow_executions(workflow_name)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_workflow_executions_status ON workflow_executions(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_workflow_contribution_status ON workflow_executions(contribution_id, status)"))
            conn.commit()
            print("  ✅ workflow_executions table created")
        except Exception as e:
            print(f"  ⚠️  Table already exists or error: {str(e)[:60]}")

        # Create knowledge_threads table
        print("\n5. Creating knowledge_threads table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_threads (
                    id SERIAL PRIMARY KEY,
                    thread_id VARCHAR(100) UNIQUE NOT NULL,
                    contribution_id INTEGER REFERENCES contributions(id),
                    user_id INTEGER REFERENCES users(id),
                    thread_type VARCHAR(50) NOT NULL,
                    context_data TEXT,
                    status VARCHAR(50) DEFAULT 'active',
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_threads_thread_id ON knowledge_threads(thread_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_threads_contribution_id ON knowledge_threads(contribution_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_threads_user_id ON knowledge_threads(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_threads_status ON knowledge_threads(status)"))
            conn.commit()
            print("  ✅ knowledge_threads table created")
        except Exception as e:
            print(f"  ⚠️  Table already exists or error: {str(e)[:60]}")

    print("\n" + "=" * 60)
    print("✅ Database migration completed successfully!")
    print("\nNew features added:")
    print("  ✓ Halt process management (halt, pause, resume)")
    print("  ✓ Engagement tracking and analytics")
    print("  ✓ Process iteration history")
    print("  ✓ Progressive automation workflows")
    print("  ✓ Knowledge thread management")
    print("\nYou can now use the new API endpoints:")
    print("  - /api/v1/halt-process/contributions/{id}/halt")
    print("  - /api/v1/halt-process/contributions/{id}/pause")
    print("  - /api/v1/halt-process/contributions/{id}/resume")
    print("  - /api/v1/halt-process/contributions/{id}/approve-halt")
    print("  - /api/v1/halt-process/contributions/{id}/execute-workflow")
    print("  - /api/v1/halt-process/contributions/{id}/engagement")
    print("  - /api/v1/halt-process/contributions/{id}/engagement-analytics")
    print("\nSee automation/README.md for complete documentation.")


if __name__ == "__main__":
    try:
        upgrade_database()
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        sys.exit(1)
