"""add_is_admin_to_users_table

Revision ID: e170c0cf2751
Revises: 71c3f5e5c075
Create Date: 2024-10-23 21:58:18.594396

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e170c0cf2751"
down_revision: Union[str, None] = "71c3f5e5c075"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column(
            "is_admin", sa.Boolean(), nullable=False, server_default="0"
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "is_admin")
    # ### end Alembic commands ###
