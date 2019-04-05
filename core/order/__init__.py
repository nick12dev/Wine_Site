# pylint: disable=fixme,invalid-name
from celery import Celery

from core import config

celery_app = Celery(
    'orders',
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_BROKER_URL
)
celery_app.conf.task_routes = {
    'core.order.order_manager.*': {'queue': 'orders'},
    'core.cognito_sync.*': {'queue': 'orders'},  # TODO otereshchenko: configure 'users' queue ?
}
