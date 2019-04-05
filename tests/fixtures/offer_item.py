# pylint: disable=unused-argument,too-many-arguments
from decimal import Decimal

from pytest import fixture

from core.db.models import db
from core.db.models.offer_item import OfferItem


@fixture
def offer_item(user, master_product_1, product_offer, order, source_1, theme_1):
    item = OfferItem(
        product_offer_id=product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights=['Highlights'],
        varietals=['Varietals'],
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def proposed_to_user_offer_item(
        user, master_product_1, proposed_to_user_product_offer, proposed_to_user_order, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=proposed_to_user_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights=['Highlights'],
        varietals=['Varietals'],
        prof_reviews=[
            {'score': 90,
             'name': 'reviewer 1 2'},
            {'score': 80,
             'name': 'reviewer 1 1'},
        ],
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def placed_offer_item(
        user, master_product_1, placed_product_offer, placed_order, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=placed_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights=['Highlights'],
        varietals=['Varietals'],
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def accepted_offer_item(
        user, master_product_1, accepted_product_offer, support_notified_order, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=accepted_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights=['Highlights'],
        varietals=['Varietals'],
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def approved_offer_item(
        user, master_product_1, approved_product_offer, approved_order, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=approved_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights='["Highlights"]',
        varietals='["Varietals"]',
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def support_notified_offer_item_1(
        user, master_product_1, support_notified_product_offer, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=support_notified_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(70),
        description='Short description',
        location='Region',
        brand='brand',
        highlights='["Highlights"]',
        varietals='["Varietals"]',
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def support_notified_offer_item_2(
        user, master_product_1, support_notified_product_offer, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=support_notified_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(60),
        description='Short description',
        location='Region',
        brand='brand',
        highlights='["Highlights"]',
        varietals='["Varietals"]',
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def old_accepted_offer_item_1(
        user, master_product_1, old_accepted_product_offer, old_completed_order, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=old_accepted_product_offer.id,
        master_product_id=master_product_1.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights=['Highlights'],
        varietals=['Varietals'],
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def old_accepted_offer_item_2(
        user, master_product_2, old_accepted_product_offer, old_completed_order, source_1, theme_1
):
    item = OfferItem(
        product_offer_id=old_accepted_product_offer.id,
        master_product_id=master_product_2.id,
        name='wine name',
        score_num=99,
        image='img_url',
        price=Decimal(80),
        description='Short description',
        location='Region',
        brand='brand',
        highlights=['Highlights'],
        varietals=['Varietals'],
        sku='123',
        qoh=1,
        msrp=Decimal('3.99'),
        product_url='http://product',
        best_theme=theme_1,
    )
    db.session.add(item)
    db.session.commit()

    yield item


@fixture
def product_dict_1(master_product_1, theme_1):
    return {
        'master_product_id': master_product_1.id,
        'price': '10',
        'wine_type': 'wine_type',
        'rating': '90',
        'qpr': 'qpr',
        'wine_name': 'wine_name1',
        'region': 'region',
        'varietals': ['varietals'],
        'highlights': ['highlight1', 'highlight2'],
        'img_url': 'img_url',
        'brand': 'brand',
        'short_desc': 'short_desc',
        'sku': 'sku1',
        'qoh': 1,
        'msrp': 3.99,
        'product_url': 'http://product',
        'best_theme': theme_1.id,
    }


@fixture
def product_dict_2(master_product_2, theme_1):
    return {
        'master_product_id': master_product_2.id,
        'price': '11',
        'wine_type': 'wine_type',
        'rating': '89',
        'qpr': 'qpr',
        'wine_name': 'wine_name2',
        'region': 'region',
        'varietals': ['varietals'],
        'highlights': ['highlight1', 'highlight2'],
        'img_url': 'img_url',
        'brand': 'brand',
        'short_desc': 'short_desc',
        'sku': 'sku2',
        'qoh': 1,
        'msrp': 3.99,
        'product_url': 'http://product',
        'best_theme': theme_1.id,
    }


@fixture
def product_dict_3(master_product_3, theme_1):
    return {
        'master_product_id': master_product_3.id,
        'price': '13',
        'wine_type': 'wine_type',
        'rating': '88',
        'qpr': 'qpr',
        'wine_name': 'wine_name3',
        'region': 'region',
        'varietals': ['varietals'],
        'highlights': ['highlight1', 'highlight2'],
        'img_url': 'img_url',
        'brand': 'brand',
        'short_desc': 'short_desc',
        'sku': 'sku3',
        'qoh': 1,
        'msrp': 3.99,
        'product_url': 'http://product',
        'best_theme': theme_1.id,
    }


@fixture
def product_dict_4(master_product_4, theme_1):
    return {
        'master_product_id': master_product_4.id,
        'price': '19.99',
        'wine_type': 'wine_type',
        'rating': '88',
        'qpr': 'qpr',
        'wine_name': 'wine_name4',
        'region': 'region',
        'varietals': ['varietals'],
        'highlights': ['highlight1', 'highlight2'],
        'img_url': 'img_url',
        'brand': 'brand',
        'short_desc': 'short_desc',
        'sku': 'sku4',
        'qoh': 1,
        'msrp': 21.99,
        'product_url': 'http://product',
        'best_theme': theme_1.id,
    }
