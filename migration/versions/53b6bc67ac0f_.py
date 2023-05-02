"""empty message

Revision ID: 53b6bc67ac0f
Revises: e6796b2526c2
Create Date: 2023-05-02 09:55:24.377143

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '53b6bc67ac0f'
down_revision = 'e6796b2526c2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('schedules', 'time',
               existing_type=postgresql.TIME(),
               nullable=False)
    op.drop_constraint('schedules_chat_id_key', 'schedules', type_='unique')
    op.create_unique_constraint('unique_time_for_chat', 'schedules', ['chat_id', 'time'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_time_for_chat', 'schedules', type_='unique')
    op.create_unique_constraint('schedules_chat_id_key', 'schedules', ['chat_id'])
    op.alter_column('schedules', 'time',
               existing_type=postgresql.TIME(),
               nullable=True)
    # ### end Alembic commands ###