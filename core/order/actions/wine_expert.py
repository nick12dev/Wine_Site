# pylint: disable=too-few-public-methods
import logging

from core.db.models import (
    PROPOSED_TO_WINE_EXPERT_STATE,
    NOTIFY_USER_ACTION,
    APPROVED_STATE,
)
from core.order.actions.base import (
    Action,
    send_mail,
    get_admin_order_url,
)
from core.dbmethods import get_wine_expert_for_order


class NotifyWineExpertAction(Action):

    def run(self, order_id):
        expert = get_wine_expert_for_order(order_id)
        logging.info('sending notification to wine expert: %s', expert.email)

        order_url = get_admin_order_url(order_id)
        msg = 'New order %s is available here: %s' % (order_id, order_url)
        send_mail(expert.email, 'New Order', msg)

        return None, PROPOSED_TO_WINE_EXPERT_STATE


class ApproveAction(Action):

    def run(self, order_id):
        logging.info('approving order: %s', order_id)
        return NOTIFY_USER_ACTION, APPROVED_STATE
