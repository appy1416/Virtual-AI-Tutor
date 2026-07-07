"""create quizzes notes chat analytics voice and learning twin tables

Revision ID: 003
Revises: 002
Create Date: 2026-07-05 19:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sqldev

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create quizzes table
    op.create_table(
        'quizzes',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('lesson_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('question_text', sqldev.String(length=5000), nullable=False),
        sqldev.Column('quiz_type', sqldev.String(length=50), nullable=False, server_default='mcq'),
        sqldev.Column('options', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('correct_answer', sqldev.String(length=1000), nullable=True),
        sqldev.Column('difficulty_level', sqldev.Integer(), nullable=False, server_default='5'),
        sqldev.Column('max_attempts', sqldev.Integer(), nullable=False, server_default='3'),
        sqldev.Column('time_limit_seconds', sqldev.Integer(), nullable=True),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('deleted_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 2. Create quiz_answers table
    op.create_table(
        'quiz_answers',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('quiz_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('user_answer', sqldev.String(length=5000), nullable=False),
        sqldev.Column('is_correct', sqldev.Boolean(), nullable=True),
        sqldev.Column('confidence_level', sqldev.Integer(), nullable=True),
        sqldev.Column('time_spent_seconds', sqldev.Integer(), nullable=False, server_default='0'),
        sqldev.Column('feedback', sqldev.String(length=5000), nullable=True),
        sqldev.Column('attempted_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 3. Create notes table
    op.create_table(
        'notes',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('lesson_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('content', sqldev.String(length=100000), nullable=False),
        sqldev.Column('ai_summary', sqldev.String(length=10000), nullable=True),
        sqldev.Column('word_count', sqldev.Integer(), nullable=False, server_default='0'),
        sqldev.Column('tags', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('deleted_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 4. Create chat_histories table
    op.create_table(
        'chat_histories',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('lesson_id', sqldev.String(length=36), nullable=True),
        sqldev.Column('course_id', sqldev.String(length=36), nullable=True),
        sqldev.Column('messages', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('ai_model', sqldev.String(length=100), nullable=False, server_default='openai'),
        sqldev.Column('started_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('ended_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.Column('message_count', sqldev.Integer(), nullable=False, server_default='0'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='SET NULL'),
        sqldev.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='SET NULL'),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 5. Create analytics_events table
    op.create_table(
        'analytics_events',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('event_type', sqldev.String(length=100), nullable=False),
        sqldev.Column('metadata', sqldev.JSON(), nullable=False, server_default='{}'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 6. Create student_performances table
    op.create_table(
        'student_performances',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('lesson_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('quiz_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('score', sqldev.Integer(), nullable=False),
        sqldev.Column('accuracy', sqldev.Integer(), nullable=False),
        sqldev.Column('time_spent_seconds', sqldev.Integer(), nullable=False, server_default='0'),
        sqldev.Column('completion_status', sqldev.String(length=50), nullable=False, server_default='completed'),
        sqldev.Column('mastery_level', sqldev.Integer(), nullable=False, server_default='0'),
        sqldev.Column('completed_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sqldev.ForeignKeyConstraint(['quiz_id'], ['quizzes.id'], ondelete='CASCADE'),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 7. Create recommendations table
    op.create_table(
        'recommendations',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('recommendation_type', sqldev.String(length=50), nullable=False),
        sqldev.Column('target_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('target_title', sqldev.String(length=200), nullable=False, server_default='Untitled'),
        sqldev.Column('reason', sqldev.String(length=1000), nullable=False),
        sqldev.Column('relevance_score', sqldev.Integer(), nullable=False, server_default='50'),
        sqldev.Column('clicked', sqldev.Boolean(), nullable=False, server_default='0'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 8. Create voice_sessions table
    op.create_table(
        'voice_sessions',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('tutor_type', sqldev.String(length=50), nullable=False, server_default='ai_voice'),
        sqldev.Column('lesson_id', sqldev.String(length=36), nullable=True),
        sqldev.Column('audio_url', sqldev.String(length=512), nullable=True),
        sqldev.Column('transcription', sqldev.String(length=10000), nullable=True),
        sqldev.Column('ai_response_audio', sqldev.String(length=512), nullable=True),
        sqldev.Column('duration_seconds', sqldev.Integer(), nullable=False, server_default='0'),
        sqldev.Column('audio_quality', sqldev.String(length=50), nullable=False, server_default='medium'),
        sqldev.Column('started_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('ended_at', sqldev.DateTime(timezone=True), nullable=True),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='SET NULL'),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id')
    )

    # 9. Create learning_twins table
    op.create_table(
        'learning_twins',
        sqldev.Column('id', sqldev.String(length=36), nullable=False),
        sqldev.Column('student_id', sqldev.String(length=36), nullable=False),
        sqldev.Column('learning_style', sqldev.String(length=50), nullable=False, server_default='mixed'),
        sqldev.Column('knowledge_gaps', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('next_review_items', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('recommended_courses', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('career_goals', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('learning_pace', sqldev.String(length=50), nullable=False, server_default='normal'),
        sqldev.Column('preferred_study_times', sqldev.JSON(), nullable=False, server_default='{}'),
        sqldev.Column('preferred_study_duration_minutes', sqldev.Integer(), nullable=False, server_default='45'),
        sqldev.Column('strengths', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('weaknesses', sqldev.JSON(), nullable=False, server_default='[]'),
        sqldev.Column('created_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.Column('updated_at', sqldev.DateTime(timezone=True), nullable=False, server_default=sqldev.text('CURRENT_TIMESTAMP')),
        sqldev.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sqldev.PrimaryKeyConstraint('id'),
        sqldev.UniqueConstraint('student_id', name='uq_learning_twin_student')
    )

    # Indices
    op.create_index('idx_quiz_lesson', 'quizzes', ['lesson_id'], unique=False)
    op.create_index('idx_answer_student', 'quiz_answers', ['student_id'], unique=False)
    op.create_index('idx_note_student', 'notes', ['student_id'], unique=False)
    op.create_index('idx_chat_student', 'chat_histories', ['student_id'], unique=False)
    op.create_index('idx_event_student_type', 'analytics_events', ['student_id', 'event_type'], unique=False)
    op.create_index('idx_event_created', 'analytics_events', ['created_at'], unique=False)
    op.create_index('idx_perf_student', 'student_performances', ['student_id'], unique=False)
    op.create_index('idx_rec_student', 'recommendations', ['student_id'], unique=False)
    op.create_index('idx_voice_student', 'voice_sessions', ['student_id'], unique=False)

def downgrade() -> None:
    op.drop_index('idx_voice_student', table_name='voice_sessions')
    op.drop_index('idx_rec_student', table_name='recommendations')
    op.drop_index('idx_perf_student', table_name='student_performances')
    op.drop_index('idx_event_created', table_name='analytics_events')
    op.drop_index('idx_event_student_type', table_name='analytics_events')
    op.drop_index('idx_chat_student', table_name='chat_histories')
    op.drop_index('idx_note_student', table_name='notes')
    op.drop_index('idx_answer_student', table_name='quiz_answers')
    op.drop_index('idx_quiz_lesson', table_name='quizzes')

    op.drop_table('learning_twins')
    op.drop_table('voice_sessions')
    op.drop_table('recommendations')
    op.drop_table('student_performances')
    op.drop_table('analytics_events')
    op.drop_table('chat_histories')
    op.drop_table('notes')
    op.drop_table('quiz_answers')
    op.drop_table('quizzes')
