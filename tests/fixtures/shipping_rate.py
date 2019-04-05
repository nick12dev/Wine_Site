from pytest import fixture

from core.db.models import db
from core.db.models.shipping_rate import ShippingRate


@fixture
def shipping_rate(source_location):
    rate = ShippingRate(
        source_location_id=source_location.id,
        from_postcode=0,
        to_postcode=9999,
        bottle_qty=2,
        shipping_cost=10
    )

    db.session.add(rate)
    db.session.commit()

    return rate


@fixture
def shipping_rate_2(source_location_2):
    rate = ShippingRate(
        source_location_id=source_location_2.id,
        from_postcode=1233,
        to_postcode=1235,
        bottle_qty=2,
        shipping_cost=20
    )

    db.session.add(rate)
    db.session.commit()

    return rate


@fixture
def shipping_rate_3(source_location):
    rate = ShippingRate(
        source_location_id=source_location.id,
        from_postcode=1233,
        to_postcode=1235,
        bottle_qty=4,
        shipping_cost=25
    )

    db.session.add(rate)
    db.session.commit()

    return rate
