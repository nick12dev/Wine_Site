# pylint: disable=fixme,no-member
import logging
import traceback

from core.order import celery_app
from core.dbmethods import (
    create_order,
    move_order,
    get_order,
    get_orders_to_run,
    get_timed_out_orders,
    get_wine_expert_for_order,
)

from core.order.actions import (
    SearchAction,
    NotifyWineExpertAction,
    NotifyUserAction,
    ApproveAction,
    AcceptOfferAction,
    NotifyAcceptedOrder,
    PlaceOrderAction,
    SetShippedAction,
    CaptureMoneyAction,
    NotifyUserShippedAction,
    CompleteAction,
    NotifyExceptionAction,
)
from core.order.actions.base import (
    send_mail,
    get_admin_order_url,
)
from core.db.models import (
    db,
    SEARCH_ACTION,
    STARTED_STATE,
    NOTIFY_WINE_EXPERT_ACTION,
    READY_TO_PROPOSE_STATE,
    APPROVE_ACTION,
    NOTIFY_USER_ACTION,
    PROPOSED_TO_WINE_EXPERT_STATE,
    PROPOSED_TO_USER_STATE,
    ACCEPT_ACTION,
    APPROVED_STATE,
    OFFER_ACCEPTED_STATE,
    NOTIFY_ACCEPTED_OFFER_ACTION,
    SUPPORT_NOTIFIED_STATE,
    PLACE_ORDER_ACTION,
    ORDER_PLACED_STATE,
    SET_SHIPPED_ACTION,
    ORDER_SHIPPED_STATE,
    CAPTURE_MONEY_ACTION,
    MONEY_CAPTURED_STATE,
    NOTIFY_USER_SHIPPED_ACTION,
    USER_NOTIFIED_SHIPPED_STATE,
    SET_USER_RECEIVED_ACTION,
    USER_RECEIVED_STATE,
    COMPLETE_ACTION,
    COMPLETED_STATE,
    NOTIFY_EXCEPTION_ACTION,
    EXCEPTION_TO_NOTIFY_STATE,
    EXCEPTION_STATE,
    SEARCH_EXCEPTION_TO_NOTIFY_STATE,
    SEARCH_EXCEPTION_STATE,
    RETRY_SEARCH_ACTION,
    EXCEPTION_TO_NOTIFY_STATE_SET,
    EXCEPTION_STATE_SET,
    NOTIFY_WINE_EXPERT_EXCEPTION_TO_NOTIFY_STATE,
    NOTIFY_WINE_EXPERT_EXCEPTION_STATE,
    AUTHORIZE_PAYMENT_EXCEPTION_TO_NOTIFY_STATE,
    AUTHORIZE_PAYMENT_EXCEPTION_STATE,
    NOTIFY_ACCEPTED_OFFER_EXCEPTION_TO_NOTIFY_STATE,
    NOTIFY_ACCEPTED_OFFER_EXCEPTION_STATE,
    CAPTURE_MONEY_EXCEPTION_TO_NOTIFY_STATE,
    CAPTURE_MONEY_EXCEPTION_STATE,
    NEXT_MONTH_ORDER_EXCEPTION_TO_NOTIFY_STATE,
    NEXT_MONTH_ORDER_EXCEPTION_STATE,
)
from core.db.models.order import Order
from core.order.actions.search import RetrySearchAction
from core.order.actions.support_admin import SetUserReceivedAction
from core.order.exceptions import OrderException

VALID_STATE_ACTIONS = {
    STARTED_STATE: {SEARCH_ACTION},
    READY_TO_PROPOSE_STATE: {NOTIFY_WINE_EXPERT_ACTION, RETRY_SEARCH_ACTION},
    PROPOSED_TO_WINE_EXPERT_STATE: {APPROVE_ACTION, RETRY_SEARCH_ACTION},
    APPROVED_STATE: {NOTIFY_USER_ACTION, RETRY_SEARCH_ACTION},
    PROPOSED_TO_USER_STATE: {ACCEPT_ACTION, RETRY_SEARCH_ACTION},
    OFFER_ACCEPTED_STATE: {NOTIFY_ACCEPTED_OFFER_ACTION},
    SUPPORT_NOTIFIED_STATE: {PLACE_ORDER_ACTION},
    ORDER_PLACED_STATE: {SET_SHIPPED_ACTION},
    ORDER_SHIPPED_STATE: {CAPTURE_MONEY_ACTION},
    MONEY_CAPTURED_STATE: {NOTIFY_USER_SHIPPED_ACTION},
    USER_NOTIFIED_SHIPPED_STATE: {SET_USER_RECEIVED_ACTION},
    USER_RECEIVED_STATE: {COMPLETE_ACTION},
    EXCEPTION_TO_NOTIFY_STATE: {RETRY_SEARCH_ACTION},
    EXCEPTION_STATE: {RETRY_SEARCH_ACTION},
    SEARCH_EXCEPTION_TO_NOTIFY_STATE: {RETRY_SEARCH_ACTION},
    SEARCH_EXCEPTION_STATE: {RETRY_SEARCH_ACTION},
    NOTIFY_WINE_EXPERT_EXCEPTION_TO_NOTIFY_STATE: {RETRY_SEARCH_ACTION},
    NOTIFY_WINE_EXPERT_EXCEPTION_STATE: {RETRY_SEARCH_ACTION},
    AUTHORIZE_PAYMENT_EXCEPTION_TO_NOTIFY_STATE: {RETRY_SEARCH_ACTION},
    AUTHORIZE_PAYMENT_EXCEPTION_STATE: {RETRY_SEARCH_ACTION},
    NOTIFY_ACCEPTED_OFFER_EXCEPTION_TO_NOTIFY_STATE: {RETRY_SEARCH_ACTION},
    NOTIFY_ACCEPTED_OFFER_EXCEPTION_STATE: {RETRY_SEARCH_ACTION},
    CAPTURE_MONEY_EXCEPTION_TO_NOTIFY_STATE: {RETRY_SEARCH_ACTION},
    CAPTURE_MONEY_EXCEPTION_STATE: {RETRY_SEARCH_ACTION},
    NEXT_MONTH_ORDER_EXCEPTION_TO_NOTIFY_STATE: set(),
    NEXT_MONTH_ORDER_EXCEPTION_STATE: set(),
}
for exception_state in EXCEPTION_TO_NOTIFY_STATE_SET:
    VALID_STATE_ACTIONS.setdefault(exception_state, set()).add(NOTIFY_EXCEPTION_ACTION)

VALID_MANUAL_STATE_ACTIONS = {
    STARTED_STATE: (),
    READY_TO_PROPOSE_STATE: (RETRY_SEARCH_ACTION,),
    PROPOSED_TO_WINE_EXPERT_STATE: (APPROVE_ACTION, RETRY_SEARCH_ACTION),
    APPROVED_STATE: (RETRY_SEARCH_ACTION,),
    PROPOSED_TO_USER_STATE: (RETRY_SEARCH_ACTION,),
    OFFER_ACCEPTED_STATE: (),
    SUPPORT_NOTIFIED_STATE: (PLACE_ORDER_ACTION,),
    ORDER_PLACED_STATE: (SET_SHIPPED_ACTION,),
    ORDER_SHIPPED_STATE: (),
    MONEY_CAPTURED_STATE: (),
    USER_NOTIFIED_SHIPPED_STATE: (SET_USER_RECEIVED_ACTION,),
    USER_RECEIVED_STATE: (),
    COMPLETED_STATE: (),
    EXCEPTION_TO_NOTIFY_STATE: (RETRY_SEARCH_ACTION,),
    EXCEPTION_STATE: (RETRY_SEARCH_ACTION,),
    SEARCH_EXCEPTION_TO_NOTIFY_STATE: (RETRY_SEARCH_ACTION,),
    SEARCH_EXCEPTION_STATE: (RETRY_SEARCH_ACTION,),
    NOTIFY_WINE_EXPERT_EXCEPTION_TO_NOTIFY_STATE: (RETRY_SEARCH_ACTION,),
    NOTIFY_WINE_EXPERT_EXCEPTION_STATE: (RETRY_SEARCH_ACTION,),
    AUTHORIZE_PAYMENT_EXCEPTION_TO_NOTIFY_STATE: (RETRY_SEARCH_ACTION,),
    AUTHORIZE_PAYMENT_EXCEPTION_STATE: (RETRY_SEARCH_ACTION,),
    NOTIFY_ACCEPTED_OFFER_EXCEPTION_TO_NOTIFY_STATE: (RETRY_SEARCH_ACTION,),
    NOTIFY_ACCEPTED_OFFER_EXCEPTION_STATE: (RETRY_SEARCH_ACTION,),
    CAPTURE_MONEY_EXCEPTION_TO_NOTIFY_STATE: (RETRY_SEARCH_ACTION,),
    CAPTURE_MONEY_EXCEPTION_STATE: (RETRY_SEARCH_ACTION,),
    NEXT_MONTH_ORDER_EXCEPTION_TO_NOTIFY_STATE: (),
    NEXT_MONTH_ORDER_EXCEPTION_STATE: (),
}

USER_PROPOSED_ORDER_STATES = (
    PROPOSED_TO_USER_STATE,
)
USER_UPCOMING_ORDER_STATES = (
    OFFER_ACCEPTED_STATE,
    SUPPORT_NOTIFIED_STATE,
    ORDER_PLACED_STATE,
    ORDER_SHIPPED_STATE,
    MONEY_CAPTURED_STATE,
    USER_NOTIFIED_SHIPPED_STATE,
)
USER_ORDER_HISTORY_STATES = (
    USER_RECEIVED_STATE,
    COMPLETED_STATE,
)


@celery_app.task
def run_scheduled_orders():
    logging.info('running run_scheduled_orders')
    orders = get_orders_to_run()
    for order in orders:
        run_order.delay(order.id)


@celery_app.task
def run_order(order_id, action=None):
    OrderManager(order_id).run_action(action=action)


@celery_app.task
def notify_timed_out_orders():
    orders = get_timed_out_orders()

    if not orders:
        return

    expert = get_wine_expert_for_order(orders[0])

    order_states = []
    for order in orders:
        order.timed_out = True
        db.session.add(order)
        order_states.append(
            '{0:{fill}{align}10} {1:{fill}{align}35} {2}'.format(
                order.id, order.state, get_admin_order_url(order.id), fill=' ', align='<'
            )
        )
    db.session.commit()

    msg = "Following Orders are in timed out state:\n %s" % '\n'.join(order_states)
    send_mail(expert.email, 'Timed out Orders', msg)

    db.session.close()


class OrderManager:
    """
    Order state transitions:

    started -> ready_to_propose -> proposed_to_wine_expert -> approved_by_expert ->

        -> proposed_to_user -> offer_accepted -> support_notified_accepted_offer->

        -> order_placed -> order_shipped -> money_captured -> user_notified_shipped ->

        -> user_received -> completed

    """
    ACTIONS = {
        SEARCH_ACTION: SearchAction,
        NOTIFY_WINE_EXPERT_ACTION: NotifyWineExpertAction,
        APPROVE_ACTION: ApproveAction,
        NOTIFY_USER_ACTION: NotifyUserAction,
        ACCEPT_ACTION: AcceptOfferAction,
        NOTIFY_ACCEPTED_OFFER_ACTION: NotifyAcceptedOrder,
        PLACE_ORDER_ACTION: PlaceOrderAction,
        SET_SHIPPED_ACTION: SetShippedAction,
        CAPTURE_MONEY_ACTION: CaptureMoneyAction,
        NOTIFY_USER_SHIPPED_ACTION: NotifyUserShippedAction,
        SET_USER_RECEIVED_ACTION: SetUserReceivedAction,
        COMPLETE_ACTION: CompleteAction,
        NOTIFY_EXCEPTION_ACTION: NotifyExceptionAction,
        RETRY_SEARCH_ACTION: RetrySearchAction,
    }
    EXCEPTIONS = {
        SEARCH_ACTION: SEARCH_EXCEPTION_TO_NOTIFY_STATE,
        NOTIFY_WINE_EXPERT_ACTION: NOTIFY_WINE_EXPERT_EXCEPTION_TO_NOTIFY_STATE,
        ACCEPT_ACTION: AUTHORIZE_PAYMENT_EXCEPTION_TO_NOTIFY_STATE,
        NOTIFY_ACCEPTED_OFFER_ACTION: NOTIFY_ACCEPTED_OFFER_EXCEPTION_TO_NOTIFY_STATE,
        CAPTURE_MONEY_ACTION: CAPTURE_MONEY_EXCEPTION_TO_NOTIFY_STATE,
        COMPLETE_ACTION: NEXT_MONTH_ORDER_EXCEPTION_TO_NOTIFY_STATE,
    }

    def __init__(self, order_or_id):
        if isinstance(order_or_id, Order):
            self.order = order_or_id
        else:
            self.order = get_order(order_or_id)

    @classmethod
    def create_order(cls, user_id, subscription_id):
        order = create_order(
            user_id=user_id,
            subscription_id=subscription_id
        )
        return cls(order.id)

    def run_action(self, action=None):
        _action = action or self.order.action

        if not self._is_action_valid(_action):
            raise RuntimeError(
                'Invalid action: {} for state: {}'.format(
                    _action, self.order.state
                )
            )

        try:
            logging.info('running action: %s', _action)
            next_action, next_state = self.ACTIONS[_action]().run(self.order.id)
            if next_state in EXCEPTION_STATE_SET:
                exception_msg = self.order.exception_message
            else:
                exception_msg = None
        except Exception as e:

            db.session.rollback()

            if isinstance(e, OrderException):
                msg = e.msg
            else:
                msg = traceback.format_exc()
            logging.exception('Error while executing action: %s', _action)
            next_action = NOTIFY_EXCEPTION_ACTION
            next_state = self.EXCEPTIONS.get(_action, EXCEPTION_TO_NOTIFY_STATE)
            exception_msg = "Error while executing action: %s, for order: %s.\n\nException: %s" % (
                _action, self.order.id, msg
            )

        self.order = move_order(
            self.order, action=next_action, state=next_state, exception_msg=exception_msg
        )

        if self.order.action is None:
            return

        self.run_action()

    def _is_action_valid(self, action):
        return action in VALID_STATE_ACTIONS[self.order.state]
