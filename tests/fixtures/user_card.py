# pylint: disable=no-member
from pytest import fixture

from core.db.models import db
from core.db.models.user_card import UserCard


@fixture
def user_card_1(user, domain_card_1):
    card = UserCard(
        user_id=user.id,
        card_id=domain_card_1.id,
        value=1
    )
    db.session.add(card)
    db.session.commit()

    yield card


@fixture
def user_card_2(user, domain_card_2):
    card = UserCard(
        user_id=user.id,
        card_id=domain_card_2.id,
        value=-1
    )
    db.session.add(card)
    db.session.commit()

    yield card


@fixture
def user_card_3(user, domain_card_3):
    card = UserCard(
        user_id=user.id,
        card_id=domain_card_3.id,
        value=0
    )
    db.session.add(card)
    db.session.commit()

    yield card
