# pylint: disable=unused-import,invalid-name,wrong-import-position
import gevent.monkey

gevent.monkey.patch_all()

import logging

from celery.schedules import crontab

from core import (
    config,
    cognito_sync,
)
from core.startup import create_app
from core.order import (
    celery_app,
    order_manager,
)

app = create_app()
app.app_context().push()

cognito_user_sync_cron_exp = config.COGNITO_USER_SYNC_CRON_EXP.split()
if len(cognito_user_sync_cron_exp) != 5:
    raise ValueError(
        'config.COGNITO_USER_SYNC_CRON_EXP should consist of 5 space-separated members '
        '(minute hour day-of-week day-of-month month-of-year) but "%s" was received instead',
        config.COGNITO_USER_SYNC_CRON_EXP
    )
logging.info('cognito_user_sync_cron_exp = %r', cognito_user_sync_cron_exp)

celery_app.conf.beat_schedule = {
    'get-orders-to-run': {
        'task': 'core.order.order_manager.run_scheduled_orders',
        'schedule': 300,  # 5 minutes
    },
    'notify-timed-out-orders': {
        'task': 'core.order.order_manager.notify_timed_out_orders',
        'schedule': 3600,  # 1 hour
    },
    'bulk-load-cognito-user-attributes': {
        'task': 'core.cognito_sync.run_full_cognito_user_sync',
        'schedule': crontab(
            minute=cognito_user_sync_cron_exp[0],
            hour=cognito_user_sync_cron_exp[1],
            day_of_week=cognito_user_sync_cron_exp[2],
            day_of_month=cognito_user_sync_cron_exp[3],
            month_of_year=cognito_user_sync_cron_exp[4],
        ),
    },
}
