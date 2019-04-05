# pylint: disable=no-member
from pytest import fixture
from datetime import datetime

from core.db.models import db
from core.db.models.user_subscription import UserSubscription


@fixture
def user_subscription(user):
    subscription = UserSubscription(
        user_id=user.id,
        type='mixed',
        budget=100,
        bottle_qty=2
    )
    db.session.add(subscription)
    db.session.commit()

    user.primary_user_subscription_id = subscription.id
    db.session.commit()

    yield subscription


@fixture
def user_subscription_last_order_20150530(user):
    subscription = UserSubscription(
        user_id=user.id,
        type='mixed',
        budget=100,
        bottle_qty=2,
        last_order_searched_at=datetime(2015, 5, 30, 13, 13, 13, 13)
    )
    db.session.add(subscription)
    db.session.commit()

    user.primary_user_subscription_id = subscription.id
    db.session.commit()

    yield subscription


@fixture
def user_subscription2(user2):
    subscription = UserSubscription(
        user_id=user2.id,
        type='red',
        budget=100,
        bottle_qty=2
    )
    db.session.add(subscription)
    db.session.commit()

    user2.primary_user_subscription_id = subscription.id
    db.session.commit()

    yield subscription


@fixture
def user_subscription_proposed(user):
    subscription = UserSubscription(
        user_id=user.id,
        type='mixed'
    )
    db.session.add(subscription)
    db.session.commit()

    user.primary_user_subscription_id = subscription.id
    db.session.commit()

    yield subscription
