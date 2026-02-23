"""add genre, anime_genres, users and user_anime_list tables

Revision ID: a1b2c3d4e5f6
Revises: b366de7a638c
Create Date: 2026-02-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b366de7a638c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'genre',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('mal_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('mal_id'),
    )
    op.create_index('ix_genre_mal_id', 'genre', ['mal_id'], unique=True)

    op.create_table(
        'anime_genres',
        sa.Column('anime_id', sa.Integer(), nullable=False),
        sa.Column('genre_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['anime_id'], ['anime.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['genre_id'], ['genre.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('anime_id', 'genre_id'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'user_anime_list',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('anime_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'watching', 'completed', 'plan_to_watch', 'dropped', 'on_hold',
                name='watchstatus'
            ),
            nullable=False,
        ),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['anime_id'], ['anime.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'anime_id', name='uq_user_anime'),
        sa.CheckConstraint('score >= 0 AND score <= 10', name='ck_score_range'),
        sa.CheckConstraint('progress >= 0', name='ck_progress_non_negative'),
    )
    op.create_index('ix_user_anime_list_user_id', 'user_anime_list', ['user_id'])
    op.create_index('ix_user_anime_list_anime_id', 'user_anime_list', ['anime_id'])


def downgrade() -> None:
    op.drop_index('ix_user_anime_list_anime_id', table_name='user_anime_list')
    op.drop_index('ix_user_anime_list_user_id', table_name='user_anime_list')
    op.drop_table('user_anime_list')
    op.execute("DROP TYPE IF EXISTS watchstatus")
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('anime_genres')
    op.drop_index('ix_genre_mal_id', table_name='genre')
    op.drop_table('genre')
