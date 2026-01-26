"""
Reindex xAPI Statements to Elasticsearch

Management command to bulk index existing xAPI Statements
to Elasticsearch for fast search and aggregation.

Usage:
    python manage.py reindex_statements
    python manage.py reindex_statements --batch-size=500
    python manage.py reindex_statements --dry-run
"""

from django.core.management.base import BaseCommand
from django.conf import settings

from lrs.models import XAPIStatement


class Command(BaseCommand):
    help = 'Reindex xAPI Statements to Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of statements per bulk request (default: 500)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually indexing (preview only)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reindex even if document exists',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        force = options['force']

        # Check if Elasticsearch is configured
        es_host = getattr(settings, 'ELASTICSEARCH_HOST', None)
        if not es_host:
            self.stdout.write(self.style.WARNING(
                'ELASTICSEARCH_HOST not configured in settings. Skipping Elasticsearch indexing.'
            ))
            return

        try:
            from lrs.elasticsearch import get_client, STATEMENT_INDEX, index_statement_to_dict
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Could not import elasticsearch module: {e}'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No documents will be indexed'))

        # Check Elasticsearch connection
        es_client = get_client()
        if not es_client:
            self.stdout.write(self.style.ERROR('Cannot connect to Elasticsearch'))
            return
        self.stdout.write(self.style.SUCCESS('Connected to Elasticsearch'))

        # Get total count
        total = XAPIStatement.objects.count()
        self.stdout.write(f'Found {total} statements to index')

        if total == 0:
            self.stdout.write('No statements to index')
            return

        # Process in batches
        indexed = 0
        errors = 0
        skipped = 0

        statements = XAPIStatement.objects.all().order_by('timestamp')

        batch = []
        for i, stmt in enumerate(statements.iterator(chunk_size=batch_size)):
            doc = index_statement_to_dict(stmt)
            batch.append({
                '_index': STATEMENT_INDEX,
                '_id': str(stmt.id),
                '_source': doc,
            })

            if len(batch) >= batch_size:
                if not dry_run:
                    success, failed = self._bulk_index(es_client, batch, force)
                    indexed += success
                    errors += failed
                else:
                    indexed += len(batch)
                batch = []

                # Progress
                progress = ((i + 1) / total) * 100
                self.stdout.write(f'Progress: {i + 1}/{total} ({progress:.1f}%)')

        # Index remaining batch
        if batch:
            if not dry_run:
                success, failed = self._bulk_index(es_client, batch, force)
                indexed += success
                errors += failed
            else:
                indexed += len(batch)

        # Refresh index
        if not dry_run and indexed > 0:
            try:
                es_client.indices.refresh(index=STATEMENT_INDEX)
                self.stdout.write('Index refreshed')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not refresh index: {e}'))

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Reindex Summary:'))
        self.stdout.write(f'  Total statements: {total}')
        self.stdout.write(f'  Successfully indexed: {indexed}')
        self.stdout.write(f'  Errors: {errors}')
        self.stdout.write(f'  Skipped: {skipped}')

    def _bulk_index(self, es_client, batch, force):
        """Perform bulk indexing."""
        from elasticsearch.helpers import bulk, BulkIndexError

        success = 0
        failed = 0

        try:
            # Use bulk helper
            if force:
                # Delete and re-create
                actions = []
                for item in batch:
                    actions.append({
                        '_op_type': 'index',
                        '_index': item['_index'],
                        '_id': item['_id'],
                        '_source': item['_source'],
                    })
                success_count, errors = bulk(
                    es_client,
                    actions,
                    raise_on_error=False,
                    raise_on_exception=False,
                )
                success = success_count
                if errors:
                    failed = len(errors)
            else:
                # Create only if not exists
                actions = []
                for item in batch:
                    actions.append({
                        '_op_type': 'create',
                        '_index': item['_index'],
                        '_id': item['_id'],
                        '_source': item['_source'],
                    })
                try:
                    success_count, errors = bulk(
                        es_client,
                        actions,
                        raise_on_error=False,
                        raise_on_exception=False,
                    )
                    success = success_count
                    if errors:
                        # Filter out "document already exists" errors
                        real_errors = [
                            e for e in errors
                            if 'version_conflict_engine_exception' not in str(e)
                        ]
                        failed = len(real_errors)
                except BulkIndexError as e:
                    # Some documents may already exist
                    success = len(batch) - len(e.errors)
                    failed = len(e.errors)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Bulk index error: {e}'))
            failed = len(batch)

        return success, failed
