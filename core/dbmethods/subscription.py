# pylint: disable=no-member
import logging

from core.dbmethods import (
    create_order,
    get_current_order,
)
from core.db.models import db
from core.db.models.user_subscription import UserSubscription


def create_subscription(user_id, subscription_dct):
    logging.info('create_subscription: user_id: %s', user_id)
    subscription = UserSubscription(
        user_id=user_id,
        type=subscription_dct.get('type'),
        bottle_qty=subscription_dct.get('bottle_qty'),
        budget=subscription_dct.get('budget_decimal'),
        state=subscription_dct.get('state')
    )
    db.session.add(subscription)
    db.session.commit()

    return subscription


def update_subscription(user_id, subscription, subscription_dct):
    logging.info(
        'update_subscription: user_id: %s, subscription_id: %s',
        user_id, subscription.id
    )

    def set_value(model, attr, value):
        if value:
            setattr(model, attr, value)

    set_value(subscription, 'type', subscription_dct.get('type'))
    set_value(subscription, 'bottle_qty', subscription_dct.get('bottle_qty'))
    set_value(subscription, 'budget', subscription_dct.get('budget'))
    set_value(subscription, 'state', subscription_dct.get('state'))
    db.session.commit()

    if subscription_dct.get('apply_for_current_order'):
        order = get_current_order(user_id)

        if order.is_active:
            db.session.delete(order)
            db.session.commit()
            create_order(user_id, subscription.id)


def save_subscription(user_id, subscription_dct):
    logging.info('save_subscription: user_id: %s; %s', user_id, subscription_dct)
    subscription = db.session.query(
        UserSubscription
    ).filter_by(user_id=user_id).first()

    if subscription:
        update_subscription(user_id, subscription, subscription_dct)
    else:
        subscription = create_subscription(user_id, subscription_dct)

    return subscription
