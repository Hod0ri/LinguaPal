"""
Backfill xAPI Statements

Management command to convert existing GanaQuiz and WordQuiz data
to xAPI Statements for historical data migration.

Usage:
    python manage.py backfill_statements
    python manage.py backfill_statements --quiz-type=gana
    python manage.py backfill_statements --quiz-type=word
    python manage.py backfill_statements --dry-run
"""

import uuid
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from words.models import GanaQuiz, GanaQuizQuestion, WordQuiz, WordQuizQuestion
from lrs.models import XAPIStatement
from lrs.constants import (
    XAPIVerb,
    XAPIActivityType,
    QuizType,
    LINGUAPAL_BASE_IRI,
    DEFAULT_MASTERY_SCORE,
)


class Command(BaseCommand):
    help = 'Backfill xAPI Statements from existing quiz data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiz-type',
            type=str,
            choices=['gana', 'word', 'all'],
            default='all',
            help='Quiz type to backfill (default: all)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without creating statements (preview only)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of quizzes to process per batch (default: 100)',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip quizzes that already have statements (default: True)',
        )

    def handle(self, *args, **options):
        quiz_type = options['quiz_type']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        skip_existing = options['skip_existing']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No statements will be created'))

        stats = {
            'gana_quizzes': 0,
            'gana_statements': 0,
            'word_quizzes': 0,
            'word_statements': 0,
            'skipped': 0,
            'errors': 0,
        }

        if quiz_type in ['gana', 'all']:
            self.backfill_gana_quizzes(dry_run, batch_size, skip_existing, stats)

        if quiz_type in ['word', 'all']:
            self.backfill_word_quizzes(dry_run, batch_size, skip_existing, stats)

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Backfill Summary:'))
        self.stdout.write(f"  Gana Quizzes processed: {stats['gana_quizzes']}")
        self.stdout.write(f"  Gana Statements created: {stats['gana_statements']}")
        self.stdout.write(f"  Word Quizzes processed: {stats['word_quizzes']}")
        self.stdout.write(f"  Word Statements created: {stats['word_statements']}")
        self.stdout.write(f"  Skipped (existing): {stats['skipped']}")
        self.stdout.write(f"  Errors: {stats['errors']}")
        total_statements = stats['gana_statements'] + stats['word_statements']
        self.stdout.write(f"  Total statements: {total_statements}")

    def backfill_gana_quizzes(self, dry_run, batch_size, skip_existing, stats):
        """Backfill statements for GanaQuiz records."""
        self.stdout.write('\nProcessing Gana Quizzes...')

        quizzes = GanaQuiz.objects.select_related('user').prefetch_related(
            'questions__word'
        ).order_by('id')

        total = quizzes.count()
        self.stdout.write(f'  Found {total} quizzes')

        for i, quiz in enumerate(quizzes.iterator(chunk_size=batch_size)):
            if i % 10 == 0:
                self.stdout.write(f'  Processing quiz {i + 1}/{total}...')

            # Check if already processed
            if skip_existing:
                existing = XAPIStatement.objects.filter(
                    object_id=f"{LINGUAPAL_BASE_IRI}/quiz/{QuizType.GANA_QUIZ}/{quiz.id}",
                    verb_id=XAPIVerb.INITIALIZED,
                ).exists()
                if existing:
                    stats['skipped'] += 1
                    continue

            try:
                statements = self._create_gana_quiz_statements(quiz, dry_run)
                stats['gana_quizzes'] += 1
                stats['gana_statements'] += len(statements)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error processing quiz {quiz.id}: {e}'))
                stats['errors'] += 1

    def backfill_word_quizzes(self, dry_run, batch_size, skip_existing, stats):
        """Backfill statements for WordQuiz records."""
        self.stdout.write('\nProcessing Word Quizzes...')

        quizzes = WordQuiz.objects.select_related(
            'user', 'learning_language', 'native_language'
        ).prefetch_related('questions__word').order_by('id')

        total = quizzes.count()
        self.stdout.write(f'  Found {total} quizzes')

        for i, quiz in enumerate(quizzes.iterator(chunk_size=batch_size)):
            if i % 10 == 0:
                self.stdout.write(f'  Processing quiz {i + 1}/{total}...')

            # Check if already processed
            if skip_existing:
                existing = XAPIStatement.objects.filter(
                    object_id=f"{LINGUAPAL_BASE_IRI}/quiz/{QuizType.WORD_QUIZ}/{quiz.id}",
                    verb_id=XAPIVerb.INITIALIZED,
                ).exists()
                if existing:
                    stats['skipped'] += 1
                    continue

            try:
                statements = self._create_word_quiz_statements(quiz, dry_run)
                stats['word_quizzes'] += 1
                stats['word_statements'] += len(statements)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error processing quiz {quiz.id}: {e}'))
                stats['errors'] += 1

    @transaction.atomic
    def _create_gana_quiz_statements(self, quiz, dry_run):
        """Create xAPI statements for a single GanaQuiz."""
        statements = []
        registration = uuid.uuid4()
        user = quiz.user
        category = QuizType.GANA_QUIZ
        object_id = f"{LINGUAPAL_BASE_IRI}/quiz/{category}/{quiz.id}"

        # 1. INITIALIZED statement
        if not dry_run:
            stmt = XAPIStatement.objects.create(
                actor_user=user,
                actor_mbox=user.email,
                actor_name=user.username or user.email,
                verb_id=XAPIVerb.INITIALIZED,
                verb_display='initialized',
                object_id=object_id,
                object_definition={
                    'type': XAPIActivityType.ASSESSMENT,
                    'name': {'ko': f'가나 퀴즈 #{quiz.id}'},
                    'description': {'ko': f'{quiz.get_character_set_display()} {quiz.get_quiz_type_display()}'},
                },
                context_registration=registration,
                context_extensions={
                    'quiz_type': quiz.quiz_type,
                    'character_set': quiz.character_set,
                    'total_questions': quiz.total_questions,
                },
                timestamp=quiz.started_at,
            )
            statements.append(stmt)
        else:
            statements.append({'verb': 'initialized', 'quiz_id': quiz.id})

        # 2. ANSWERED statements for each question
        for question in quiz.questions.filter(answered_at__isnull=False):
            question_object_id = f"{LINGUAPAL_BASE_IRI}/quiz/{category}/{quiz.id}/question/{question.id}"

            if not dry_run:
                stmt = XAPIStatement.objects.create(
                    actor_user=user,
                    actor_mbox=user.email,
                    actor_name=user.username or user.email,
                    verb_id=XAPIVerb.ANSWERED,
                    verb_display='answered',
                    object_id=question_object_id,
                    object_definition={
                        'type': XAPIActivityType.QUESTION,
                        'name': {'ko': f'문제 #{question.question_number}'},
                    },
                    result_success=question.is_correct,
                    result_response=question.user_answer,
                    context_registration=registration,
                    context_extensions={
                        'question_number': question.question_number,
                        'correct_answer': question.correct_answer,
                        'word': question.word.text if question.word else None,
                    },
                    timestamp=question.answered_at,
                )
                statements.append(stmt)
            else:
                statements.append({'verb': 'answered', 'question_id': question.id})

        # 3. COMPLETED and PASSED/FAILED statements if quiz is completed
        if quiz.is_completed and quiz.completed_at:
            score_scaled = quiz.correct_count / quiz.total_questions if quiz.total_questions > 0 else 0
            passed = score_scaled >= DEFAULT_MASTERY_SCORE

            if not dry_run:
                # COMPLETED
                stmt = XAPIStatement.objects.create(
                    actor_user=user,
                    actor_mbox=user.email,
                    actor_name=user.username or user.email,
                    verb_id=XAPIVerb.COMPLETED,
                    verb_display='completed',
                    object_id=object_id,
                    object_definition={
                        'type': XAPIActivityType.ASSESSMENT,
                        'name': {'ko': f'가나 퀴즈 #{quiz.id}'},
                    },
                    result_completion=True,
                    result_score_scaled=score_scaled,
                    result_score_raw=quiz.correct_count,
                    result_score_min=0,
                    result_score_max=quiz.total_questions,
                    context_registration=registration,
                    context_extensions={'quiz_type': quiz.quiz_type},
                    timestamp=quiz.completed_at,
                )
                statements.append(stmt)

                # PASSED or FAILED
                stmt = XAPIStatement.objects.create(
                    actor_user=user,
                    actor_mbox=user.email,
                    actor_name=user.username or user.email,
                    verb_id=XAPIVerb.PASSED if passed else XAPIVerb.FAILED,
                    verb_display='passed' if passed else 'failed',
                    object_id=object_id,
                    object_definition={
                        'type': XAPIActivityType.ASSESSMENT,
                        'name': {'ko': f'가나 퀴즈 #{quiz.id}'},
                    },
                    result_success=passed,
                    result_score_scaled=score_scaled,
                    context_registration=registration,
                    context_extensions={'mastery_score': DEFAULT_MASTERY_SCORE},
                    timestamp=quiz.completed_at,
                )
                statements.append(stmt)
            else:
                statements.append({'verb': 'completed', 'quiz_id': quiz.id})
                statements.append({'verb': 'passed' if passed else 'failed', 'quiz_id': quiz.id})

        return statements

    @transaction.atomic
    def _create_word_quiz_statements(self, quiz, dry_run):
        """Create xAPI statements for a single WordQuiz."""
        statements = []
        registration = uuid.uuid4()
        user = quiz.user
        category = QuizType.WORD_QUIZ
        object_id = f"{LINGUAPAL_BASE_IRI}/quiz/{category}/{quiz.id}"

        # 1. INITIALIZED statement
        if not dry_run:
            stmt = XAPIStatement.objects.create(
                actor_user=user,
                actor_mbox=user.email,
                actor_name=user.username or user.email,
                verb_id=XAPIVerb.INITIALIZED,
                verb_display='initialized',
                object_id=object_id,
                object_definition={
                    'type': XAPIActivityType.ASSESSMENT,
                    'name': {'ko': f'단어 퀴즈 #{quiz.id}'},
                    'description': {'ko': f'{quiz.learning_language.name_ko} {quiz.get_quiz_type_display()}'},
                },
                context_registration=registration,
                context_extensions={
                    'quiz_type': quiz.quiz_type,
                    'learning_language': quiz.learning_language.code,
                    'native_language': quiz.native_language.code,
                    'total_questions': quiz.total_questions,
                },
                timestamp=quiz.started_at,
            )
            statements.append(stmt)
        else:
            statements.append({'verb': 'initialized', 'quiz_id': quiz.id})

        # 2. ANSWERED statements for each question
        for question in quiz.questions.filter(answered_at__isnull=False):
            question_object_id = f"{LINGUAPAL_BASE_IRI}/quiz/{category}/{quiz.id}/question/{question.id}"

            # Get correct answer
            correct_answer = question.get_correct_answer(quiz.native_language)

            if not dry_run:
                stmt = XAPIStatement.objects.create(
                    actor_user=user,
                    actor_mbox=user.email,
                    actor_name=user.username or user.email,
                    verb_id=XAPIVerb.ANSWERED,
                    verb_display='answered',
                    object_id=question_object_id,
                    object_definition={
                        'type': XAPIActivityType.QUESTION,
                        'name': {'ko': f'문제 #{question.question_number}'},
                    },
                    result_success=question.is_correct,
                    result_response=question.user_answer,
                    context_registration=registration,
                    context_extensions={
                        'question_number': question.question_number,
                        'correct_answer': correct_answer,
                        'word': question.word.text if question.word else None,
                    },
                    timestamp=question.answered_at,
                )
                statements.append(stmt)
            else:
                statements.append({'verb': 'answered', 'question_id': question.id})

        # 3. COMPLETED and PASSED/FAILED statements if quiz is completed
        if quiz.is_completed and quiz.completed_at:
            score_scaled = quiz.correct_count / quiz.total_questions if quiz.total_questions > 0 else 0
            passed = score_scaled >= DEFAULT_MASTERY_SCORE

            if not dry_run:
                # COMPLETED
                stmt = XAPIStatement.objects.create(
                    actor_user=user,
                    actor_mbox=user.email,
                    actor_name=user.username or user.email,
                    verb_id=XAPIVerb.COMPLETED,
                    verb_display='completed',
                    object_id=object_id,
                    object_definition={
                        'type': XAPIActivityType.ASSESSMENT,
                        'name': {'ko': f'단어 퀴즈 #{quiz.id}'},
                    },
                    result_completion=True,
                    result_score_scaled=score_scaled,
                    result_score_raw=quiz.correct_count,
                    result_score_min=0,
                    result_score_max=quiz.total_questions,
                    context_registration=registration,
                    context_extensions={
                        'quiz_type': quiz.quiz_type,
                        'learning_language': quiz.learning_language.code,
                    },
                    timestamp=quiz.completed_at,
                )
                statements.append(stmt)

                # PASSED or FAILED
                stmt = XAPIStatement.objects.create(
                    actor_user=user,
                    actor_mbox=user.email,
                    actor_name=user.username or user.email,
                    verb_id=XAPIVerb.PASSED if passed else XAPIVerb.FAILED,
                    verb_display='passed' if passed else 'failed',
                    object_id=object_id,
                    object_definition={
                        'type': XAPIActivityType.ASSESSMENT,
                        'name': {'ko': f'단어 퀴즈 #{quiz.id}'},
                    },
                    result_success=passed,
                    result_score_scaled=score_scaled,
                    context_registration=registration,
                    context_extensions={'mastery_score': DEFAULT_MASTERY_SCORE},
                    timestamp=quiz.completed_at,
                )
                statements.append(stmt)
            else:
                statements.append({'verb': 'completed', 'quiz_id': quiz.id})
                statements.append({'verb': 'passed' if passed else 'failed', 'quiz_id': quiz.id})

        return statements
