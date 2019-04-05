# pylint: disable=unused-argument,no-member
from decimal import Decimal
import datetime

from pytest import fixture

from core.db.models.offer_item import OfferItem
from core.db.models.product_offer import ProductOffer
from core.dbmethods import (
    create_order,
    move_order,
)
from core.db.models import (
    db,
    PROPOSED_TO_WINE_EXPERT_STATE,
    PROPOSED_TO_USER_STATE,
    OFFER_ACCEPTED_STATE,
    COMPLETED_STATE,
    ORDER_PLACED_STATE,
    SUPPORT_NOTIFIED_STATE,
    USER_NOTIFIED_SHIPPED_STATE,
    EXCEPTION_TO_NOTIFY_STATE,
    EXCEPTION_STATE,
)


@fixture
def order(user, user_subscription, user_address):
    _order = create_order(user.id, user_subscription.id)

    yield _order


@fixture
def order2(user2, user_subscription2, user_address2):
    _order = create_order(user2.id, user_subscription2.id)

    yield _order


@fixture
def order_proposed(user, user_subscription_proposed, user_address):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, PROPOSED_TO_WINE_EXPERT_STATE)

    yield _order


@fixture
def timed_out_order(user, user_subscription_proposed, user_address):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, PROPOSED_TO_WINE_EXPERT_STATE)
    _order.state_changed_at = datetime.datetime.utcnow() - datetime.timedelta(days=3)
    db.session.commit()

    yield _order


@fixture
def placed_order(user, user_subscription_proposed, user_address):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, ORDER_PLACED_STATE)

    yield _order


@fixture
def proposed_to_user_order(user, user_subscription_proposed, user_address):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, PROPOSED_TO_USER_STATE)

    yield _order


@fixture
def proposed_to_wine_expert_order(
        user, user_subscription_proposed, user_address, source_1, master_product_1, theme_1
):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, PROPOSED_TO_WINE_EXPERT_STATE)

    _populate_product_offers(_order, source_1, master_product_1, theme_1)

    yield _order


@fixture
def accepted_order(
        user, user_subscription_proposed, user_address, source_1, master_product_1, theme_1
):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, OFFER_ACCEPTED_STATE)

    _populate_product_offers(_order, source_1, master_product_1, theme_1)

    yield _order


@fixture
def old_completed_order(user, user_subscription_proposed, user_address, source_1, master_product_1):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, COMPLETED_STATE)

    yield _order


@fixture
def support_notified_order(
        user, user_subscription_proposed, user_address, source_1, order_shipping_method_1
):
    _order = create_order(user.id, user_subscription_proposed.id)
    _order = move_order(_order, None, SUPPORT_NOTIFIED_STATE)
    _order.shipping_method_id = order_shipping_method_1.id
    db.session.commit()

    yield _order


@fixture
def order_20150515(
        user, user_subscription, user_address, source_1
):
    _order = create_order(
        user.id,
        user_subscription.id,
        scheduled_for=datetime.datetime(2015, 5, 15, 13, 13, 13, 13),
    )

    yield _order


@fixture
def exception_to_notify_order_20150515(
        user, user_subscription, user_address, source_1
):
    _order = create_order(
        user.id,
        user_subscription.id,
    )
    _order = move_order(_order, None, EXCEPTION_TO_NOTIFY_STATE)

    _order.state_changed_at = datetime.datetime(2015, 5, 15, 13, 13, 13, 13)
    _order.scheduled_for = None
    db.session.commit()

    yield _order


@fixture
def exception_order_20150515(
        user, user_subscription, user_address, source_1
):
    _order = create_order(
        user.id,
        user_subscription.id,
    )
    _order = move_order(_order, None, EXCEPTION_STATE)

    _order.state_changed_at = datetime.datetime(2015, 5, 15, 13, 13, 13, 13)
    _order.scheduled_for = None
    db.session.commit()

    yield _order


@fixture
def user_notified_shipped_order_20150530(
        user, user_subscription_last_order_20150530, user_address, source_1
):
    _order = create_order(user.id, user_subscription_last_order_20150530.id)
    _order = move_order(_order, None, USER_NOTIFIED_SHIPPED_STATE)

    yield _order


@fixture
def completed_orders(
        user, user_subscription_proposed, user_address, source_1, master_product_1, theme_1
):
    orders = []
    for i in range(4):
        _order = create_order(user.id, user_subscription_proposed.id)
        _order.shipping_name = _order.shipping_name + str(i)
        _order = move_order(_order, None, COMPLETED_STATE)
        _order.created_at = datetime.datetime(2000 + i, 10, 10, 12, 2, 38, 784862)
        _order.state_changed_at = datetime.datetime(2010 + i, 10, 10, 12, 2, 38, 784862)

        _populate_product_offers(_order, source_1, master_product_1, theme_1)
        orders.append(_order)

    yield orders


def _populate_product_offers(_order, source, master_product, best_theme):
    offer1 = ProductOffer(
        order_id=_order.id,
        source_id=source.id,
        wine_type=_order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=10,
        name=source.name
    )
    db.session.add(offer1)
    db.session.flush()
    _populate_offer_items(offer1, master_product, best_theme)

    offer2 = ProductOffer(
        accepted=True,
        order_id=_order.id,
        source_id=source.id,
        wine_type=_order.subscription.type,
        bottle_qty=2,
        total_cost=98,
        priority=11,
        name=source.name
    )
    db.session.add(offer2)
    db.session.flush()
    _populate_offer_items(offer2, master_product, best_theme)


def _populate_offer_items(offer, master_product, best_theme):
    for i in range(3):
        item = OfferItem(
            product_offer_id=offer.id,
            master_product_id=master_product.id,
            name='wine name' + str(i),
            score_num=99 + i,
            image='img_url',
            price=Decimal(80 + 1),
            description='Short description',
            location='Region',
            brand='brand',
            highlights=['Highlights'],
            varietals=['Varietals'],
            sku='123',
            qoh=1,
            msrp=Decimal('3.99'),
            product_url='http://product',
            best_theme=best_theme,
        )
        db.session.add(item)
    db.session.commit()
