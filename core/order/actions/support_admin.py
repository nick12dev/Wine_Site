import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from core.order.actions.base import (
    Action,
    send_mail,
    send_template_email,
    get_admin_order_url,
)
# from core.order.actions.user import send_silent_push
from core.db.models import (
    SUPPORT_NOTIFIED_STATE,
    ORDER_PLACED_STATE,
    ORDER_SHIPPED_STATE,
    USER_RECEIVED_STATE,
    COMPLETED_STATE,
    EXCEPTION_TO_NOTIFY_STATE,
    EXCEPTION_STATE,
    EXCEPTION_STATE_NOTIFY_MAPPING,
    CAPTURE_MONEY_ACTION,
    COMPLETE_ACTION,
)
from core.dbmethods import (
    get_wine_expert_for_order,
    get_order,
    create_order,
)
from core.dbmethods.product import get_accepted_product_offer
from core.dbmethods.user import get_user_order_data


class NotifyAcceptedOrder(Action):

    def run(self, order_id):
        logging.info('running NotifyAcceptedOrder order_id: %s', order_id)

        expert = get_wine_expert_for_order(order_id)
        product_offer = get_accepted_product_offer(order_id)
        order_url = get_admin_order_url(order_id)

        msg = "User has accepted Product Offer: %s in Order: %s. It's available here: %s" % (
            product_offer.id, order_id, order_url
        )
        send_mail(expert.email, 'Accepted Order', msg)

        return None, SUPPORT_NOTIFIED_STATE


class PlaceOrderAction(Action):

    def _send_email(self, order_id):
        order_data = get_user_order_data(order_id)
        send_template_email(
            order_data['shipping_address']['email'], 'order_placed',
            order_data
        )

    def run(self, order_id):
        logging.info('running PlaceOrderAction order_id: %s', order_id)

        try:
            self._send_email(order_id)
            #order = get_order(order_id)
            #device_tokens = [t.token for t in order.user.device_tokens]
            #send_silent_push(device_tokens)
        except Exception as e:
            logging.exception('Error when sending placed order email: %s', e)

        return None, ORDER_PLACED_STATE


class SetShippedAction(Action):

    def run(self, order_id):
        logging.info('running SetShippedAction order_id: %s', order_id)
        return CAPTURE_MONEY_ACTION, ORDER_SHIPPED_STATE


class SetUserReceivedAction(Action):

    def run(self, order_id):
        logging.info('running SetUserReceivedAction order_id: %s', order_id)
        return COMPLETE_ACTION, USER_RECEIVED_STATE


class CompleteAction(Action):

    def run(self, order_id):
        logging.info('running CompleteAction order_id: %s', order_id)
        order = get_order(order_id)

        utcnow = datetime.utcnow()
        if order.user.primary_user_subscription.last_order_searched_at is None:
            scheduled_for = utcnow
        else:
            scheduled_for = order.user.primary_user_subscription.last_order_searched_at
            scheduled_for += relativedelta(months=1)
            if scheduled_for < utcnow:
                scheduled_for = utcnow

        create_order(order.user.id, order.user.primary_user_subscription.id, scheduled_for=scheduled_for)
        return None, COMPLETED_STATE


class NotifyExceptionAction(Action):

    def run(self, order_id):
        logging.info('running NotifyExceptionAction order_id: %s', order_id)

        try:
            expert = get_wine_expert_for_order(order_id)
            order = get_order(order_id)
            new_state = EXCEPTION_STATE_NOTIFY_MAPPING.get(order.state, EXCEPTION_STATE)

            subject = 'Exception in Order: %s' % order.id
            send_mail(expert.email, subject, order.exception_message)
        except Exception:
            logging.exception('Exception in NotifyExceptionAction for order: %s', order_id)
            return None, EXCEPTION_TO_NOTIFY_STATE

        return None, new_state
