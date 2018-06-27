
def register_tasks(celery):
    from src.tasks.example_task import init_task
    init_task(celery)
