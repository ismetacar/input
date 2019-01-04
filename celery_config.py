from datetime import timedelta

CELERY_IMPORTS = ('src.tasks')
CELERY_TASK_RESULT_EXPIRES = 30000
CELERY_TIMEZONE = 'UTC'

CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERYBEAT_SCHEDULE = {
    'tasks-celery-insert': {
        'task': 'src.tasks.insert_contents_to_cms',
        'schedule': timedelta(seconds=10),
    },
    'tasks-celery-remove': {
        'task': 'src.tasks.delete_expired_contents_from_cms',
        'schedule': timedelta(minutes=2)
    }
}
