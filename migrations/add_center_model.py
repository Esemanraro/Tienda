"""Create center table and add order discount fields

Revision ID: add_center_model
Revises: add_status_to_order
Create Date: 2024-11-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime
from sqlalchemy import String, Float, DateTime

# revision identifiers, used by Alembic.
revision = 'add_center_model'
down_revision = 'add_status_to_order'
branch_labels = None
depends_on = None

centers_table = table(
    'center',
    column('slug', String),
    column('name', String),
    column('discount_percentage', Float),
    column('created_at', DateTime),
    column('updated_at', DateTime),
)


def upgrade():
    op.create_table(
        'center',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('discount_percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('discount_percentage >= 0', name='ck_center_discount_non_negative'),
        sa.CheckConstraint('discount_percentage <= 100', name='ck_center_discount_max'),
    )
    op.create_index('ix_center_slug', 'center', ['slug'], unique=True)

    op.add_column('order', sa.Column('subtotal_price', sa.Float(), nullable=False, server_default='0'))
    op.add_column('order', sa.Column('discount_percentage', sa.Float(), nullable=False, server_default='0'))
    op.add_column('order', sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('order', sa.Column('discounted_total', sa.Float(), nullable=False, server_default='0'))
    op.add_column('order', sa.Column('discount_center', sa.String(length=64), nullable=True))
    op.create_index('ix_order_discount_center', 'order', ['discount_center'], unique=False)
    op.create_check_constraint('ck_order_subtotal_non_negative', 'order', 'subtotal_price >= 0')
    op.create_check_constraint('ck_order_discount_amount_non_negative', 'order', 'discount_amount >= 0')
    op.create_check_constraint('ck_order_discount_percentage_non_negative', 'order', 'discount_percentage >= 0')
    op.create_check_constraint('ck_order_discounted_total_non_negative', 'order', 'discounted_total >= 0')
    op.create_check_constraint('ck_order_total_non_negative', 'order', 'total_price >= 0')

    op.execute("""
        UPDATE "order"
        SET subtotal_price = total_price,
            discount_amount = 0,
            discount_percentage = 0,
            discounted_total = total_price
    """)

    timestamp = datetime.utcnow()
    op.bulk_insert(
        centers_table,
        [
            {'slug': 'aguadulce', 'name': 'Aguadulce', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'anclas mall', 'name': 'Anclas Mall', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'brisas del golf', 'name': 'Brisas del Golf', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'calle 50', 'name': 'Calle 50', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'costa del este', 'name': 'Costa del Este', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'david', 'name': 'David', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'chitre', 'name': 'Chitre', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'santiago', 'name': 'Santiago', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'condado del rey', 'name': 'Condado Del Rey', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'centro autorizado arraijan', 'name': 'Centro Autorizado Arraijan', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'escuela bet yacoov', 'name': 'Escuela Bet Yacoov', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
            {'slug': 'escuela de la salle', 'name': 'Escuela De La Salle', 'discount_percentage': 0, 'created_at': timestamp, 'updated_at': timestamp},
        ]
    )

    op.alter_column('order', 'subtotal_price', server_default=None)
    op.alter_column('order', 'discount_percentage', server_default=None)
    op.alter_column('order', 'discount_amount', server_default=None)
    op.alter_column('order', 'discounted_total', server_default=None)


def downgrade():
    op.drop_constraint('ck_order_total_non_negative', 'order', type_='check')
    op.drop_constraint('ck_order_discounted_total_non_negative', 'order', type_='check')
    op.drop_constraint('ck_order_discount_percentage_non_negative', 'order', type_='check')
    op.drop_constraint('ck_order_discount_amount_non_negative', 'order', type_='check')
    op.drop_constraint('ck_order_subtotal_non_negative', 'order', type_='check')
    op.drop_index('ix_order_discount_center', table_name='order')
    op.drop_column('order', 'discount_center')
    op.drop_column('order', 'discounted_total')
    op.drop_column('order', 'discount_amount')
    op.drop_column('order', 'discount_percentage')
    op.drop_column('order', 'subtotal_price')
    op.drop_index('ix_center_slug', table_name='center')
    op.drop_table('center')
