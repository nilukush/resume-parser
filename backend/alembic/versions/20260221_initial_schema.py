"""Initial schema: resumes, parsed_resume_data, resume_corrections, resume_shares

Revision ID: 001
Revises:
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resumes table
    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('parsing_version', sa.String(length=20), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_hash')
    )
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'])
    op.create_index(op.f('ix_resumes_file_hash'), 'resumes', ['file_hash'])

    # Create parsed_resume_data table
    op.create_table(
        'parsed_resume_data',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('resume_id', postgresql.UUID(), nullable=False),
        sa.Column('personal_info', postgresql.JSONB(), nullable=False),
        sa.Column('work_experience', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('education', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('skills', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('confidence_scores', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parsed_resume_data_id'), 'parsed_resume_data', ['id'])
    op.create_index(op.f('ix_parsed_resume_data_resume_id'), 'parsed_resume_data', ['resume_id'])

    # Create resume_corrections table
    op.create_table(
        'resume_corrections',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('resume_id', postgresql.UUID(), nullable=False),
        sa.Column('field_path', sa.String(length=100), nullable=False),
        sa.Column('original_value', postgresql.JSONB(), nullable=False),
        sa.Column('corrected_value', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_corrections_id'), 'resume_corrections', ['id'])
    op.create_index(op.f('ix_resume_corrections_resume_id'), 'resume_corrections', ['resume_id'])

    # Create resume_shares table
    op.create_table(
        'resume_shares',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('resume_id', postgresql.UUID(), nullable=False),
        sa.Column('share_token', sa.String(length=64), unique=True, nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_shares_id'), 'resume_shares', ['id'])
    op.create_index(op.f('ix_resume_shares_resume_id'), 'resume_shares', ['resume_id'])
    op.create_index(op.f('ix_resume_shares_share_token'), 'resume_shares', ['share_token'])


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_index(op.f('ix_resume_shares_share_token'), table_name='resume_shares')
    op.drop_index(op.f('ix_resume_shares_resume_id'), table_name='resume_shares')
    op.drop_index(op.f('ix_resume_shares_id'), table_name='resume_shares')
    op.drop_table('resume_shares')

    op.drop_index(op.f('ix_resume_corrections_resume_id'), table_name='resume_corrections')
    op.drop_index(op.f('ix_resume_corrections_id'), table_name='resume_corrections')
    op.drop_table('resume_corrections')

    op.drop_index(op.f('ix_parsed_resume_data_resume_id'), table_name='parsed_resume_data')
    op.drop_index(op.f('ix_parsed_resume_data_id'), table_name='parsed_resume_data')
    op.drop_table('parsed_resume_data')

    op.drop_index(op.f('ix_resumes_file_hash'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_id'), table_name='resumes')
    op.drop_table('resumes')
