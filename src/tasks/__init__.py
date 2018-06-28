import celery


@celery.task()
def foo():
    print("hello!")
