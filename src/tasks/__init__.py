import datetime

from src.tasks.delete_contents import remove_contents_from_cms
from src.tasks.insert_contents import get_token, get_contents_from_agency


def init_tasks(app, celery):
    @celery.task()
    def create_contents_to_cms():
        #: check configurations per 30 seconds for run task.
        #: run insert contents to cms job if the configuration next_run_time field is less than equal to now.
        #: shift next_run_time by configuration interval value
        configs = list(app.db.configurations.find({
            'next_run_time': {
                '$lte': datetime.datetime.utcnow()
            }
        }))

        insert_contents(configs)

    @celery.task()
    def delete_expired_contents_from_cms():
        #: get contents from created by the user defined in settings via _query endpoint
        #: remove content if content status is unpublished and
        #: Now date is greater than sum of content's created_at and configuration expire field
        remove_contents_from_cms()
