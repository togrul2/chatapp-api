"""friendship_unique_constraint

Revision ID: dc28cf661924
Revises: de133ebf6c6d
Create Date: 2022-10-03 22:14:28.224420

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "dc28cf661924"
down_revision = "de133ebf6c6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        "unique_sender_receiver", "friendship", ["sender_id", "receiver_id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_sender_receiver", "friendship", type_="unique")
    # ### end Alembic commands ###
