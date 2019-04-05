# pylint: disable=no-member
from pytest import fixture

from core.db.models import db
from core.db.models.product_offer import ProductOffer


@fixture
def product_offer(order, source_1):
    offer = ProductOffer(
        order_id=order.id,
        source_id=source_1.id,
        wine_type=order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=0,
        name=source_1.name
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def proposed_to_user_product_offer(proposed_to_user_order, source_1):
    offer = ProductOffer(
        order_id=proposed_to_user_order.id,
        source_id=source_1.id,
        wine_type=proposed_to_user_order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=0,
        name=source_1.name
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def proposed_to_user_product_offer_2(proposed_to_user_order, source_1):
    offer = ProductOffer(
        order_id=proposed_to_user_order.id,
        source_id=source_1.id,
        wine_type=proposed_to_user_order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=0,
        name=source_1.name
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def accepted_product_offer(support_notified_order, source_1):
    offer = ProductOffer(
        order_id=support_notified_order.id,
        source_id=source_1.id,
        wine_type=support_notified_order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=0,
        name=source_1.name,
        accepted=True
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def placed_product_offer(placed_order, source_1):
    offer = ProductOffer(
        order_id=placed_order.id,
        source_id=source_1.id,
        wine_type=placed_order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=0,
        name=source_1.name,
        accepted=True,
        stripe_charge_id='stripe_charge_id',
        product_cost=90,
        salestax_rate=0.9,
        salestax_cost=95,
        shipping_cost=4
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def support_notified_product_offer(support_notified_order, source_1):
    offer = ProductOffer(
        order_id=support_notified_order.id,
        source_id=source_1.id,
        wine_type=support_notified_order.subscription.type,
        bottle_qty=3,
        total_cost=99,
        priority=0,
        name=source_1.name,
        accepted=True,
        stripe_charge_id='stripe_charge_id'
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def support_notified_product_offer2(support_notified_order, source_1):
    offer = ProductOffer(
        order_id=support_notified_order.id,
        source_id=source_1.id,
        wine_type=support_notified_order.subscription.type,
        bottle_qty=2,
        total_cost=98,
        priority=1,
        name=source_1.name,
        accepted=False,
        stripe_charge_id='stripe_charge_id'
    )
    db.session.add(offer)
    db.session.commit()

    yield offer


@fixture
def old_accepted_product_offer(old_completed_order, source_1):
    offer = ProductOffer(
        order_id=old_completed_order.id,
        source_id=source_1.id,
        wine_type=old_completed_order.subscription.type,
        bottle_qty=2,
        total_cost=98,
        priority=1,
        name=source_1.name,
        accepted=True,
        stripe_charge_id='stripe_charge_id'
    )
    db.session.add(offer)
    db.session.commit()

    yield offer
