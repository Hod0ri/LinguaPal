"""
Celery configuration for LinguaPal project.

This module sets up Celery with RabbitMQ as the message broker.
"""

import os
from celery import Celery
from kombu import Queue

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LinguaPal.settings')

app = Celery('LinguaPal')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Define task queues
app.conf.task_queues = (
    Queue('default', routing_key='default'),
    Queue('xapi', routing_key='xapi'),
    Queue('elasticsearch', routing_key='es'),
)

# Define task routes
app.conf.task_routes = {
    'lrs.tasks.create_statement_task': {'queue': 'xapi'},
    'lrs.tasks.index_statement_task': {'queue': 'elasticsearch'},
    'lrs.tasks.bulk_index_task': {'queue': 'elasticsearch'},
    'lrs.tasks.create_quiz_statements_task': {'queue': 'xapi'},
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    print(f'Request: {self.request!r}')
