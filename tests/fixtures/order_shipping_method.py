from pytest import fixture

from core.db.models import db
from core.db.models.order_shipping_method import OrderShippingMethod


@fixture
def order_shipping_method_1(order_shipping_carrier_1):
    shipping_method = OrderShippingMethod(
        name='GSO Ground',
        carrier_id=order_shipping_carrier_1.id
    )
    db.session.add(shipping_method)
    db.session.commit()

    yield shipping_method


@fixture
def order_shipping_method_2(order_shipping_carrier_2):
    shipping_method = OrderShippingMethod(
        name='UPS Ground',
        carrier_id=order_shipping_carrier_2.id
    )
    db.session.add(shipping_method)
    db.session.commit()

    yield shipping_method


@fixture
def order_shipping_method_3(order_shipping_carrier_3):
    shipping_method = OrderShippingMethod(
        name='FedEx Ground',
        carrier_id=order_shipping_carrier_3.id
    )
    db.session.add(shipping_method)
    db.session.commit()

    yield shipping_method
