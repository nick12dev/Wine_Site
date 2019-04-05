from pytest import fixture

from core.db.models import db
from core.db.models.order_shipping_carrier import OrderShippingCarrier


@fixture
def order_shipping_carrier_1():
    carrier = OrderShippingCarrier(
        carrier='GSO',
        tracking_url_template='https://www.gso.com/Trackshipment?TrackingNumbers={}'
    )
    db.session.add(carrier)
    db.session.commit()

    yield carrier


@fixture
def order_shipping_carrier_2():
    carrier = OrderShippingCarrier(
        carrier='UPS',
        tracking_url_template='http://wwwapps.ups.com/WebTracking/track?track=yes&trackNums={}'
    )
    db.session.add(carrier)
    db.session.commit()

    yield carrier


@fixture
def order_shipping_carrier_3():
    carrier = OrderShippingCarrier(
        carrier='FedEx',
        tracking_url_template='https://www.fedex.com/apps/fedextrack/?action=track&tracknumbers={}'
    )
    db.session.add(carrier)
    db.session.commit()

    yield carrier
