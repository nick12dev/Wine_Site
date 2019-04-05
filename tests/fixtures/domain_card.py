# pylint: disable=no-member
from pytest import fixture

from core.db.models import db
from core.db.models.domain_card import DomainCard
from core.db.models.domain_category import DomainCategory


@fixture
def domain_category(app):
    category = DomainCategory(name='test_category')

    db.session.add(category)
    db.session.commit()
    app.config['M3_DOMAIN_CATEGORY_ID'] = category.id

    yield category


@fixture
def domain_card_1(domain_category):
    card = DomainCard(
        name='card1',
        display_text='text1',
        category_id=domain_category.id,
        display_order=1
    )
    db.session.add(card)
    db.session.commit()

    yield card


@fixture
def domain_card_2(domain_category):
    card = DomainCard(
        name='card2',
        display_text='text2',
        category_id=domain_category.id,
        display_order=2
    )
    db.session.add(card)
    db.session.commit()

    yield card


@fixture
def domain_card_3(domain_category):
    card = DomainCard(
        name='card3',
        display_text='text3',
        category_id=domain_category.id,
        display_order=3
    )
    db.session.add(card)
    db.session.commit()

    yield card
