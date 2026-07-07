"""create courses and lessons tables

Revision ID: 002
Revises: 001
Create Date: 2026-07-05 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sqldev

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create courses table
    op.create_table(
        'courses',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('tutor_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('title', sqldev.String(length=200), nullable=False),
        sqldev.Column('description', sqldev.String(length=1000), nullable=False),
        sqldev.Column('category', sqldev.String(length=100), nullable=False),
        sqldev.Column('level', sqldev.String(length=50), nullable=False),
        sqldev.Column('thumbnail_url', sqldev.String(length=512), nullable=True),
        sqldev.Column('max_students', sqldev.Integer(), nullable=True),
        sqldev.Column('is_published', sqldev.Boolean(), nullable=False, server_default='0'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('deleted_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.ForeignKeyConstraint(['tutor_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )
    
    # 2. Create lessons table
    op.create_table(
        'lessons',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('course_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('sequence_order', sqldev.Integer(), nullable=False),
        sqldev.Column('title', sqldev.String(length=200), nullable=False),
        sqldev.Column('description', sqldev.String(length=500), nullable=False),
        sqldev.Column('content', sqldev.String(length=10000), nullable=False),
        sqldev.Column('learning_objectives', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('estimated_duration_minutes', sqldev.Integer(), nullable=False, server_default='30'),
        sqldev.Column('difficulty_score', sqldev.Integer(), nullable=False, server_default='5'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('deleted_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id'),
        sqldev.UniqueConstraint('course_id', 'sequence_order', name='uq_course_lesson_sequence')
    )
    
    # 3. Create user_courses enrollment table
    op.create_table(
        'user_courses',
        sqldev.Column('user_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('course_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('enrolled_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('completed_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sqldev.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('user_id', 'course_id')
    )
    
    # 4. Create lesson completions table
    op.create_table(
        'lesson_completions',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('user_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('lesson_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('completed_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sqldev.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id'),
        sqldev.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_completion')
    )

    # 5. Create indices
    op.create_index('idx_course_tutor_published', 'courses', ['tutor_id', 'is_published'], unique=False)
    op.create_index('idx_course_deleted_at', 'courses', ['deleted_at'], unique=False)
    op.create_index('idx_lesson_course', 'lessons', ['course_id'], unique=False)
    op.create_index('idx_lesson_sequence', 'lessons', ['sequence_order'], unique=False)
    op.create_index('idx_lesson_deleted_at', 'lessons', ['deleted_at'], unique=False)
    op.create_index('idx_completion_user_lesson', 'lesson_completions', ['user_id', 'lesson_id'], unique=False)

def downgrade() -> None:
    # 1. Drop indices
    op.drop_index('idx_completion_user_lesson', table_name='lesson_completions')
    op.drop_index('idx_lesson_deleted_at', table_name='lessons')
    op.drop_index('idx_lesson_sequence', table_name='lessons')
    op.drop_index('idx_lesson_course', table_name='lessons')
    op.drop_index('idx_course_deleted_at', table_name='courses')
    op.drop_index('idx_course_tutor_published', table_name='courses')
    
    # 2. Drop tables
    op.drop_table('lesson_completions')
    op.drop_table('user_courses')
    op.drop_table('lessons')
    op.drop_table('courses')
