from pytest import fixture

from core.db.models import db
from core.db.models.user_address import UserAddress


@fixture
def user_address(user):
    address = UserAddress(
        user_id=user.id,
        street1='street 1',
        city='New York',
        country='US',
        postcode=1234,
        state_region='New York'
    )
    db.session.add(address)
    db.session.commit()

    user.primary_user_address_id = address.id
    db.session.commit()

    yield address


@fixture
def user_address2(user2):
    address = UserAddress(
        user_id=user2.id,
        city='New York'
    )
    db.session.add(address)
    db.session.commit()

    user2.primary_user_address_id = address.id
    db.session.commit()

    yield address
