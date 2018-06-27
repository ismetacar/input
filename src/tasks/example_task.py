def init_task(celery):
    @celery.task()
    def add_together(a, b):
        return a + b
