from pytest import fixture

from core.db.models import db
from core.db.models.source_location import SourceLocation


@fixture
def source_location(source_1):
    sl = SourceLocation(
        source_id=source_1.id,
        location_name='Location',
        ship_to_regions=['CA', 'NY']
    )

    db.session.add(sl)
    db.session.commit()

    return sl


@fixture
def source_location_2(source_2):
    sl = SourceLocation(
        source_id=source_2.id,
        location_name='Location',
        ship_to_regions=['CA', 'NY']
    )

    db.session.add(sl)
    db.session.commit()

    return sl


@fixture
def source_location_no_shipping(source_no_shipping):
    sl = SourceLocation(
        source_id=source_no_shipping.id,
        location_name='Location',
        ship_to_regions=['CA', 'NY']
    )

    db.session.add(sl)
    db.session.commit()

    return sl
