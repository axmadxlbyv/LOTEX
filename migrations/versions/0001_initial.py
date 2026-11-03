from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(64), nullable=True),
        sa.Column(
            "full_name",
            sa.String(160),
            nullable=False,
            server_default=""
        ),
        sa.Column("referrer_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        )
    )

    op.create_table(
        "uc_packages",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True
        ),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("uc_amount", sa.Integer(), nullable=False),
        sa.Column("price_uzs", sa.Integer(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        )
    )

    op.create_table(
        "orders",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id"),
            nullable=False
        ),
        sa.Column(
            "package_id",
            sa.Integer(),
            sa.ForeignKey("uc_packages.id"),
            nullable=False
        ),
        sa.Column("game_player_id", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(24),
            nullable=False,
            server_default="pending"
        ),
        sa.Column("payment_method", sa.String(24), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )


def downgrade():

    op.drop_table("orders")
    op.drop_table("uc_packages")
    op.drop_table("users")
