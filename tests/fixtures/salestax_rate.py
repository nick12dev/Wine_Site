from pytest import fixture

from core.db.models import db
from core.db.models.salestax_rate import SalestaxRate


@fixture
def salestax_rate(source_location):
    rate = SalestaxRate(
        source_location_id=source_location.id,
        from_postcode=0,
        to_postcode=100,
        taxrate=0.01
    )

    db.session.add(rate)
    rate = SalestaxRate(
        source_location_id=source_location.id,
        from_postcode=101,
        to_postcode=9999,
        taxrate=0.0925
    )

    db.session.add(rate)
    db.session.commit()

    return rate


@fixture
def salestax_rate_2(source_location_2):
    rate = SalestaxRate(
        source_location_id=source_location_2.id,
        from_postcode=0,
        to_postcode=9999,
        taxrate=0.09
    )

    db.session.add(rate)
    db.session.commit()

    return rate
