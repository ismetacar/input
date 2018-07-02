import datetime

from src.tasks.delete_contents import remove_contents_from_cms
from src.tasks.insert_contents import insert_contents


def init_tasks(app, celery, settings):
    @celery.task()
    def insert_contents_to_cms():
        #: check configurations per 30 seconds for run task.
        #: run insert contents to cms job if the configuration next_run_time field is less than or equal to now.
        #: shift next_run_time by configuration interval value
        configs = list(app.db.configurations.find({
            'next_run_time': {
                '$lte': datetime.datetime.utcnow()
            },
            'agency_name': {
                '$in': ['IHA', 'AA', 'Reuters']
            }
        }))

        for config in configs:
            app.db.configurations.find_and_modify(
                {
                    '_id': config['_id']
                },
                {
                    '$set': {
                        'next_run_time': datetime.datetime.utcnow() + datetime.timedelta(seconds=int(config['sync_at']))
                    }
                }
            )

        insert_contents(configs, settings, app.db)

    @celery.task()
    def delete_expired_contents_from_cms():
        #: get contents from created by the user defined in settings via _query endpoint
        #: remove content if content status is unpublished and
        #: Now date is greater than sum of content's created_at and configuration expire field
        configs = list(app.db.configurations.find({
            'next_run_time_for_delete': {
                '$lte': datetime.datetime.utcnow()
            },
            'agency_name': {
                '$in': ['IHA', 'AA', 'Reuters']
            }
        }))

        for config in configs:
            app.db.configurations.find_and_modify(
                {
                    '_id': config['_id']
                },
                {
                    '$set': {
                        'next_run_time_for_delete': datetime.datetime.utcnow() + datetime.timedelta(
                            minutes=int(config['expire_time']))
                    }
                }
            )

        remove_contents_from_cms(configs, settings, app.db)
