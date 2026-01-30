"""
Management command to create Elasticsearch indices for LRS.

Usage:
    python manage.py create_es_indices
    python manage.py create_es_indices --delete  # Delete and recreate
"""

from django.core.management.base import BaseCommand, CommandError

from lrs.elasticsearch import (
    create_indices,
    delete_indices,
    get_client,
    STATEMENT_INDEX,
    SESSION_INDEX,
    ACTIVITY_INDEX,
)


class Command(BaseCommand):
    help = 'Create Elasticsearch indices for xAPI statements and cmi5 sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing indices before creating new ones',
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Only check if indices exist (no creation)',
        )

    def handle(self, *args, **options):
        client = get_client()

        if not client:
            raise CommandError(
                'Elasticsearch is not available. '
                'Check ELASTICSEARCH_HOST setting and ensure Elasticsearch is running.'
            )

        self.stdout.write('Connected to Elasticsearch')

        # Check mode
        if options['check']:
            self._check_indices(client)
            return

        # Delete if requested
        if options['delete']:
            self.stdout.write(self.style.WARNING('Deleting existing indices...'))
            if delete_indices():
                self.stdout.write(self.style.SUCCESS('Indices deleted'))
            else:
                self.stdout.write(self.style.ERROR('Failed to delete indices'))

        # Create indices
        self.stdout.write('Creating indices...')

        if create_indices():
            self.stdout.write(self.style.SUCCESS('Indices created successfully'))
            self._check_indices(client)
        else:
            raise CommandError('Failed to create indices')

    def _check_indices(self, client):
        """Check and display index status."""
        self.stdout.write('\nIndex Status:')

        for index_name in [STATEMENT_INDEX, SESSION_INDEX, ACTIVITY_INDEX]:
            if client.indices.exists(index=index_name):
                # Get index stats
                stats = client.indices.stats(index=index_name)
                doc_count = stats['indices'][index_name]['primaries']['docs']['count']
                size = stats['indices'][index_name]['primaries']['store']['size_in_bytes']
                size_mb = size / (1024 * 1024)

                self.stdout.write(
                    f"  {self.style.SUCCESS('✓')} {index_name}: "
                    f"{doc_count} documents, {size_mb:.2f} MB"
                )
            else:
                self.stdout.write(
                    f"  {self.style.ERROR('✗')} {index_name}: not found"
                )
