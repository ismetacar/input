from datetime import timedelta

CELERY_IMPORTS = ('src.tasks')
CELERY_TASK_RESULT_EXPIRES = 30
CELERY_TIMEZONE = 'UTC'

CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYBEAT_SCHEDULE = {
    'tasks-celery': {
        'task': 'src.tasks.create_contents_to_cms',
        'schedule': timedelta(seconds=10),
    }
}
