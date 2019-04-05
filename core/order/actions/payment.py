import logging

from core.order.actions.base import Action
from core.dbmethods.user import (
    capture_payment,
    payment_should_be_skipped,
)
from core.db.models import (
    NOTIFY_USER_SHIPPED_ACTION,
    MONEY_CAPTURED_STATE,
)


class CaptureMoneyAction(Action):

    def run(self, order_id):
        logging.info('running CaptureMoneyAction order_id: %s', order_id)

        if payment_should_be_skipped(order_id):
            logging.info(f'Skipping CaptureMoneyAction for order: {order_id}')
        else:
            capture_payment(order_id)

        return NOTIFY_USER_SHIPPED_ACTION, MONEY_CAPTURED_STATE
