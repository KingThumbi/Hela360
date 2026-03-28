"""initial schema

Revision ID: 308fd99b1dc6
Revises:
Create Date: 2026-03-19 17:30:25.072792
"""

from alembic import op
import app.models  # noqa: F401
from app.extensions import db


# revision identifiers, used by Alembic.
revision = "308fd99b1dc6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    db.Model.metadata.create_all(bind=bind)


def downgrade():
    raise NotImplementedError("Downgrade not implemented for initial schema.")