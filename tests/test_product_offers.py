# pylint: disable=too-many-arguments,unused-argument,no-member
from decimal import Decimal
from unittest.mock import (
    patch,
    call,
)

import graphene
from graphene import Node

from core.order.actions.base import get_admin_order_url
from core.db.models import db
from core.db.models import SUPPORT_NOTIFIED_STATE
from core.db.models.product_offer import ProductOffer
from core.db.models.offer_item import OfferItem
from core.dbmethods.product import create_product_offers


def test_create_product_offers(
        app,
        order,
        product_dict_1,
        product_dict_2,
        product_dict_3,
        source_1,
        source_2,
        shipping_rate,
        shipping_rate_2,
        salestax_rate,
        salestax_rate_2,
        theme_1,
):
    products = [
        [product_dict_1, product_dict_2],
        [product_dict_3, product_dict_3],
        [product_dict_3, product_dict_3],
    ]

    # Test
    create_product_offers(order.id, products)
    db.session.commit()

    # Check
    offer_items = db.session.query(
        OfferItem
    ).join(
        OfferItem.product_offer
    ).order_by(
        OfferItem.id.asc()
    ).all()

    assert len(offer_items) == 2

    assert offer_items[0].name == 'wine_name1'
    assert offer_items[0].sku == 'sku1'
    assert offer_items[1].name == 'wine_name2'
    assert offer_items[1].sku == 'sku2'
    product_offer1 = offer_items[0].product_offer
    assert product_offer1.id == offer_items[1].product_offer.id

    assert product_offer1.order_id == order.id
    assert product_offer1.source_id == source_1.id
    assert product_offer1.bottle_qty == 2
    assert product_offer1.total_cost == Decimal('32.94')
    assert product_offer1.priority == 1
    assert product_offer1.name == 'source_1'
    assert product_offer1.salestax_rate == Decimal('0.0925')
    assert product_offer1.shipping_cost == Decimal('10')
    assert product_offer1.salestax_cost == Decimal('1.94')
    assert product_offer1.product_cost == Decimal('21')


def _assert_offer_items_are_same(offer_items, idx1, idx2):
    assert offer_items[idx1].product_offer.id == offer_items[idx2].product_offer.id
    assert offer_items[idx1].name == offer_items[idx2].name
    assert offer_items[idx1].sku == offer_items[idx2].sku
    assert offer_items[idx1].master_product_id == offer_items[idx2].master_product_id
    assert offer_items[idx1].score_num == offer_items[idx2].score_num
    assert offer_items[idx1].image == offer_items[idx2].image
    assert offer_items[idx1].description == offer_items[idx2].description
    assert offer_items[idx1].location == offer_items[idx2].location
    assert offer_items[idx1].highlights == offer_items[idx2].highlights
    assert offer_items[idx1].prof_reviews == offer_items[idx2].prof_reviews
    assert offer_items[idx1].varietals == offer_items[idx2].varietals
    assert offer_items[idx1].qty == offer_items[idx2].qty
    assert offer_items[idx1].price == offer_items[idx2].price
    assert offer_items[idx1].brand == offer_items[idx2].brand
    assert offer_items[idx1].qoh == offer_items[idx2].qoh
    assert offer_items[idx1].msrp == offer_items[idx2].msrp
    assert offer_items[idx1].product_url == offer_items[idx2].product_url
    assert offer_items[idx1].best_theme_id == offer_items[idx2].best_theme_id


@patch('core.graphql.schemas.offer_item.get_product_by_sku')
def test_replace_offer_items_by_sku(
        get_product_by_sku_m,
        app,
        order,
        product_dict_1,
        product_dict_2,
        product_dict_4,
        master_product_1,
        master_product_2,
        master_product_4,
        product_1_review_1,
        product_1_review_2,
        product_1_review_3_zero_score,
        product_2_review_1,
        source_1,
        shipping_rate_3,
        salestax_rate,
        theme_1,
        theme_2,
        theme_3,
        graphql_client_admin,
):
    master_product1_id = master_product_1.id
    master_product2_id = master_product_2.id
    master_product4_id = master_product_4.id
    products = [
        [product_dict_4, product_dict_4, product_dict_4, product_dict_4],
    ]

    create_product_offers(order.id, products)
    db.session.commit()

    offer_items = db.session.query(
        OfferItem
    ).join(
        OfferItem.product_offer
    ).order_by(
        OfferItem.id.asc()
    ).all()

    assert len(offer_items) == 4

    assert offer_items[0].name == 'wine_name4'
    assert offer_items[0].sku == 'sku4'
    assert offer_items[0].master_product_id == master_product4_id
    assert offer_items[0].score_num == 88
    assert offer_items[0].image == 'img_url'
    assert offer_items[0].description == 'short_desc'
    assert offer_items[0].location == 'region'
    assert offer_items[0].highlights == ['highlight1', 'highlight2']
    assert offer_items[0].varietals == ['varietals']
    assert offer_items[0].prof_reviews == []
    assert offer_items[0].qty is None
    assert offer_items[0].price == Decimal('19.99')
    assert offer_items[0].brand == 'brand'
    assert offer_items[0].qoh == 1
    assert offer_items[0].msrp == Decimal('21.99')
    assert offer_items[0].product_url == 'http://product'
    assert offer_items[0].best_theme_id == theme_1.id

    _assert_offer_items_are_same(offer_items, 1, 0)
    _assert_offer_items_are_same(offer_items, 2, 0)
    _assert_offer_items_are_same(offer_items, 3, 0)

    product_offer1 = offer_items[0].product_offer
    assert product_offer1.order_id == order.id
    assert product_offer1.source_id == source_1.id
    assert product_offer1.bottle_qty == 4
    assert product_offer1.total_cost == Decimal('112.36')
    assert product_offer1.priority == 1
    assert product_offer1.name == 'source_1'
    assert product_offer1.salestax_rate == Decimal('0.0925')
    assert product_offer1.shipping_cost == Decimal('25')
    assert product_offer1.salestax_cost == Decimal('7.40')
    assert product_offer1.product_cost == Decimal('79.96')

    query = '''
        mutation($input: SaveOrderInput!) {
          saveOrder(input: $input) {
            clientMutationId
            order {
              productOffers {
                edges {
                  node {
                    priority
                    name
                    wineType
                    bottleQty
                    productCost
                    salestaxCost
                    shippingCost
                    totalCost
                    offerItems {
                      edges {
                        node {
                          id
                          brand
                          name
                          scoreNum
                          image
                          description
                          location
                          qty
                          sku
                          qoh
                          productUrl
                          price
                          msrp
                          highlights
                          varietals
                          topProductReview {
                            reviewerName
                            reviewScore
                          }
                          productReviews {
                            reviewerName
                            reviewScore
                          }
                          bestTheme {
                            title}}}}}}}}}}
    '''

    def get_product_by_sku_mock(sku):
        if sku == product_dict_1['sku']:
            return product_dict_1
        if sku == product_dict_2['sku']:
            return product_dict_2
        return None

    get_product_by_sku_m.side_effect = get_product_by_sku_mock

    # Test
    res = graphql_client_admin.post(query, variables={
        'input': {
            'clientMutationId': 'replace by sku test',
            'id': Node.to_global_id('Order', order.id),
            'offerItemReplacements': [
                {
                    'offerItemId': Node.to_global_id('OfferItem', offer_items[3].id),
                    'newBestThemeId': Node.to_global_id('Theme', theme_3.id),
                },
                {
                    'offerItemId': Node.to_global_id('OfferItem', offer_items[0].id),
                    'newSku': product_dict_2['sku'],
                },
                {
                    'offerItemId': Node.to_global_id('OfferItem', offer_items[1].id),
                    'newSku': product_dict_1['sku'],
                    'newBestThemeId': Node.to_global_id('Theme', theme_2.id),
                },
            ],
        }
    })

    # Sort offer items for test stability (sorting is not always the same in response for some reason)
    res_offer_items = res.get('data', {}).get('saveOrder', {}).get(
        'order', {}
    ).get('productOffers', {}).get('edges', [{}])[0].get('node', {}).get('offerItems', {})
    res_offer_item_edges = res_offer_items.get('edges')
    if res_offer_item_edges:
        res_offer_item_edges = sorted(
            res_offer_item_edges,
            key=lambda n1: int(Node.from_global_id(n1['node']['id'])[1])
        )
        for n2 in res_offer_item_edges:
            del n2['node']['id']
        res_offer_items['edges'] = res_offer_item_edges

    # Check
    expected = {'data': {'saveOrder': {
        'clientMutationId': 'replace by sku test',
        'order': {'productOffers': {'edges': [
            {'node': {
                'bottleQty': 4,
                'name': 'source_1',
                'offerItems': {'edges': [
                    {'node': {'bestTheme': {'title': 'theme 1'},
                              'brand': 'brand',
                              'description': 'short_desc',
                              'highlights': ['highlight1',
                                             'highlight2'],
                              'image': 'img_url',
                              'location': 'region',
                              'msrp': '21.99',
                              'name': 'wine_name4',
                              'price': '19.99',
                              'productUrl': 'http://product',
                              'qoh': 1,
                              'qty': None,
                              'scoreNum': 88,
                              'sku': 'sku4',
                              'topProductReview': None,
                              'productReviews': [],
                              'varietals': ['varietals']}},
                    {'node': {'bestTheme': {'title': 'theme 3'},
                              'brand': 'brand',
                              'description': 'short_desc',
                              'highlights': ['highlight1',
                                             'highlight2'],
                              'image': 'img_url',
                              'location': 'region',
                              'msrp': '21.99',
                              'name': 'wine_name4',
                              'price': '19.99',
                              'productUrl': 'http://product',
                              'qoh': 1,
                              'qty': None,
                              'scoreNum': 88,
                              'sku': 'sku4',
                              'topProductReview': None,
                              'productReviews': [],
                              'varietals': ['varietals']}},
                    {'node': {'bestTheme': {'title': 'theme 1'},
                              'brand': 'brand',
                              'description': 'short_desc',
                              'highlights': ['highlight1',
                                             'highlight2'],
                              'image': 'img_url',
                              'location': 'region',
                              'msrp': '3.99',
                              'name': 'wine_name2',
                              'price': '11.00',
                              'productUrl': 'http://product',
                              'qoh': 1,
                              'qty': None,
                              'scoreNum': 89,
                              'sku': 'sku2',
                              'topProductReview': {'reviewScore': 78,
                                                   'reviewerName': 'reviewer 2 1'},
                              'productReviews': [{'reviewScore': 78,
                                                  'reviewerName': 'reviewer 2 1'}],
                              'varietals': ['varietals']}},
                    {'node': {'bestTheme': {'title': 'theme 2'},
                              'brand': 'brand',
                              'description': 'short_desc',
                              'highlights': ['highlight1',
                                             'highlight2'],
                              'image': 'img_url',
                              'location': 'region',
                              'msrp': '3.99',
                              'name': 'wine_name1',
                              'price': '10.00',
                              'productUrl': 'http://product',
                              'qoh': 1,
                              'qty': None,
                              'scoreNum': 90,
                              'sku': 'sku1',
                              'topProductReview': {'reviewScore': 90,
                                                   'reviewerName': 'reviewer 1 2'},
                              'productReviews': [{'reviewScore': 90,
                                                  'reviewerName': 'reviewer 1 2'},
                                                 {'reviewScore': 80,
                                                  'reviewerName': 'reviewer 1 1'}],
                              'varietals': ['varietals']}}]},
                'priority': 1,
                'productCost': '60.98',
                'salestaxCost': '5.64',
                'shippingCost': '25.00',
                'totalCost': '91.62',
                'wineType': 'mixed'}}]}}}}}
    assert res == expected

    get_product_by_sku_m.assert_has_calls([
        call('sku2'),
        call('sku1'),
    ])
    assert get_product_by_sku_m.call_count == 2

    offer_items = db.session.query(
        OfferItem
    ).join(
        OfferItem.product_offer
    ).order_by(
        OfferItem.id.asc()
    ).all()

    assert len(offer_items) == 4

    assert offer_items[0].name == 'wine_name4'
    assert offer_items[0].sku == 'sku4'
    assert offer_items[0].master_product_id == master_product4_id
    assert offer_items[0].score_num == 88
    assert offer_items[0].image == 'img_url'
    assert offer_items[0].description == 'short_desc'
    assert offer_items[0].location == 'region'
    assert offer_items[0].highlights == ['highlight1', 'highlight2']
    assert offer_items[0].varietals == ['varietals']
    assert offer_items[0].prof_reviews == []
    assert offer_items[0].qty is None
    assert offer_items[0].price == Decimal('19.99')
    assert offer_items[0].brand == 'brand'
    assert offer_items[0].qoh == 1
    assert offer_items[0].msrp == Decimal('21.99')
    assert offer_items[0].product_url == 'http://product'
    assert offer_items[0].best_theme_id == theme_1.id

    assert offer_items[1].name == 'wine_name4'
    assert offer_items[1].sku == 'sku4'
    assert offer_items[1].master_product_id == master_product4_id
    assert offer_items[1].score_num == 88
    assert offer_items[1].image == 'img_url'
    assert offer_items[1].description == 'short_desc'
    assert offer_items[1].location == 'region'
    assert offer_items[1].highlights == ['highlight1', 'highlight2']
    assert offer_items[1].varietals == ['varietals']
    assert offer_items[1].prof_reviews == []
    assert offer_items[1].qty is None
    assert offer_items[1].price == Decimal('19.99')
    assert offer_items[1].brand == 'brand'
    assert offer_items[1].qoh == 1
    assert offer_items[1].msrp == Decimal('21.99')
    assert offer_items[1].product_url == 'http://product'
    assert offer_items[1].best_theme_id == theme_3.id

    assert offer_items[2].name == 'wine_name2'
    assert offer_items[2].sku == 'sku2'
    assert offer_items[2].master_product_id == master_product2_id
    assert offer_items[2].score_num == 89
    assert offer_items[2].image == 'img_url'
    assert offer_items[2].description == 'short_desc'
    assert offer_items[2].location == 'region'
    assert offer_items[2].highlights == ['highlight1', 'highlight2']
    assert offer_items[2].varietals == ['varietals']
    assert offer_items[2].prof_reviews == [{'name': 'reviewer 2 1', 'score': 78}]
    assert offer_items[2].qty is None
    assert offer_items[2].price == Decimal('11')
    assert offer_items[2].brand == 'brand'
    assert offer_items[2].qoh == 1
    assert offer_items[2].msrp == Decimal('3.99')
    assert offer_items[2].product_url == 'http://product'
    assert offer_items[2].best_theme_id == theme_1.id

    assert offer_items[3].name == 'wine_name1'
    assert offer_items[3].sku == 'sku1'
    assert offer_items[3].master_product_id == master_product1_id
    assert offer_items[3].score_num == 90
    assert offer_items[3].image == 'img_url'
    assert offer_items[3].description == 'short_desc'
    assert offer_items[3].location == 'region'
    assert offer_items[3].highlights == ['highlight1', 'highlight2']
    assert offer_items[3].varietals == ['varietals']
    assert offer_items[3].prof_reviews == [{'name': 'reviewer 1 2', 'score': 90},
                                           {'name': 'reviewer 1 1', 'score': 80}]
    assert offer_items[3].qty is None
    assert offer_items[3].price == Decimal('10')
    assert offer_items[3].brand == 'brand'
    assert offer_items[3].qoh == 1
    assert offer_items[3].msrp == Decimal('3.99')
    assert offer_items[3].product_url == 'http://product'
    assert offer_items[3].best_theme_id == theme_2.id

    product_offer1 = offer_items[0].product_offer
    assert product_offer1.order_id == order.id
    assert product_offer1.source_id == source_1.id
    assert product_offer1.bottle_qty == 4
    assert product_offer1.total_cost == Decimal('91.62')
    assert product_offer1.priority == 1
    assert product_offer1.name == 'source_1'
    assert product_offer1.salestax_rate == Decimal('0.0925')
    assert product_offer1.shipping_cost == Decimal('25')
    assert product_offer1.salestax_cost == Decimal('5.64')
    assert product_offer1.product_cost == Decimal('60.98')


def test_create_product_offers_values(
        app,
        order,
        master_product_1,
        product_1_review_1,
        product_1_review_2,
        product_1_review_3_zero_score,
        theme_1,
        shipping_rate,
        shipping_rate_2,
        salestax_rate,
        salestax_rate_2,
):
    product_1 = {
        'master_product_id': master_product_1.id,
        'price': '10',
        'wine_type': 'wine_type',
        'rating': '90',
        'qpr': 'qpr',
        'wine_name': 'wine_name',
        'region': 'region',
        'varietals': ['varietals'],
        'highlights': ['highlight1', 'highlight2'],
        'img_url': 'img_url',
        'brand': 'brand',
        'short_desc': 'short_desc',
        'sku': 'sku',
        'qoh': 1,
        'msrp': 3.99,
        'product_url': 'http://product',
        'best_theme': theme_1.id,
    }

    products = [[product_1, product_1]]

    # Test
    create_product_offers(order.id, products)
    db.session.commit()

    # Check
    product_offer = db.session.query(
        ProductOffer
    ).filter_by(order_id=order.id).first()
    assert product_offer.salestax_rate == Decimal('0.0925')

    offer_items = db.session.query(
        OfferItem
    ).filter(
        OfferItem.master_product_id.in_(
            [master_product_1.id]
        )
    ).order_by(
        OfferItem.id.asc()
    ).all()

    assert len(offer_items) == 2
    offer_item = offer_items[0]
    assert offer_item.master_product_id == master_product_1.id
    assert offer_item.name == 'wine_name'
    assert offer_item.score_num == 90
    assert offer_item.image == 'img_url'
    assert offer_item.price == Decimal(10)
    assert offer_item.description == 'short_desc'
    assert offer_item.varietals == ['varietals']
    assert offer_item.highlights == ['highlight1', 'highlight2']
    assert offer_item.prof_reviews == [{'name': 'reviewer 1 2', 'score': 90}, {'name': 'reviewer 1 1', 'score': 80}]
    assert offer_item.location == 'region'
    assert offer_item.brand == 'brand'
    assert offer_item.sku == 'sku'
    assert offer_item.qoh == 1
    assert offer_item.msrp == Decimal('3.99')
    assert offer_item.product_url == 'http://product'
    assert offer_item.best_theme.id == theme_1.id


def test_create_product_offers_default_values(
        app, order, master_product_1, shipping_rate, shipping_rate_2, salestax_rate, salestax_rate_2
):
    product_1 = {
        'master_product_id': master_product_1.id,
        'price': '0',
        'wine_type': 'wine_type',
        'rating': '0',
        'qpr': 'qpr',
        'img_url': 'img_url',
    }

    products = [[product_1, product_1]]

    # Test
    create_product_offers(order.id, products)
    db.session.commit()

    # Check
    offer_items = db.session.query(
        OfferItem
    ).filter(
        OfferItem.master_product_id.in_(
            [master_product_1.id]
        )
    ).order_by(
        OfferItem.id.asc()
    ).all()

    assert len(offer_items) == 2
    offer_item = offer_items[0]
    assert offer_item.master_product_id == master_product_1.id
    assert offer_item.name == ''
    assert offer_item.score_num == 0
    assert offer_item.image == 'img_url'
    assert offer_item.price == Decimal(0)
    assert offer_item.description == ''
    assert offer_item.varietals is None
    assert offer_item.highlights is None
    assert offer_item.prof_reviews == []
    assert offer_item.location == ''
    assert offer_item.brand == ''
    assert offer_item.sku == ''
    assert offer_item.qoh is None
    assert offer_item.msrp is None
    assert offer_item.product_url is None
    assert offer_item.best_theme_id is None


def test_get_product_offers(
        graphql_client, user, proposed_to_user_product_offer, proposed_to_user_offer_item,
        product_1_review_1, product_1_review_2, product_1_review_3_zero_score
):
    query = """{user 
    { proposedOrder {
        productOffers {
            edges {
                node {
                    wineType
                    bottleQty
                    expertNote
                    productCost
                    salestaxCost
                    shippingCost
                    totalCost
                    name
                    offerItems {
                        edges {
                            node {
                                brand
                                name
                                description
                                scoreNum
                                image
                                location
                                qty
                                price
                                msrp
                                sku
                                qoh
                                productUrl
                                bestTheme {
                                  title
                                  shortDescription
                                  image
                                }
                                topProductReview {
                                  reviewerName
                                  reviewScore
                                }
                                productReviews {
                                  reviewerName
                                  reviewScore
                                }
                                varietals
                                highlights}}}}}}}}}
    """
    query = query.replace('\n', '')

    res = graphql_client.post(query)

    expected = {
        'data': {
            'user': {
                'proposedOrder': {
                    'productOffers': {
                        'edges': [
                            {
                                'node': {
                                    'wineType': 'mixed',
                                    'bottleQty': 3,
                                    'expertNote': None,
                                    'productCost': None,
                                    'salestaxCost': None,
                                    'shippingCost': None,
                                    'totalCost': '99.00',
                                    'name': 'source_1',
                                    'offerItems': {
                                        'edges': [
                                            {
                                                'node': {
                                                    'brand': 'brand',
                                                    'name': 'wine name',
                                                    'description': 'Short description',
                                                    'scoreNum': 99,
                                                    'image': 'img_url',
                                                    'location': 'Region',
                                                    'qty': None,
                                                    'price': '80.00',
                                                    'highlights': ['Highlights'],
                                                    'varietals': ['Varietals'],
                                                    'sku': '123',
                                                    'qoh': 1,
                                                    'msrp': '3.99',
                                                    'productUrl': 'http://product',
                                                    'topProductReview': {'reviewScore': 90,
                                                                         'reviewerName': 'reviewer 1 2'},
                                                    'productReviews': [{'reviewScore': 90,
                                                                        'reviewerName': 'reviewer 1 2'},
                                                                       {'reviewScore': 80,
                                                                        'reviewerName': 'reviewer 1 1'}],
                                                    'bestTheme': {
                                                        'title': 'theme 1',
                                                        'shortDescription': 'theme short desc 1',
                                                        'image': 'https://someimage.url',
                                                    },
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
    }

    assert res == expected


@patch('core.order.actions.support_admin.send_mail')
@patch('core.dbmethods.user.stripe')
def test_accept_product_offer(
        stripe_m, send_mail_m, graphql_client, wine_expert, user,
        proposed_to_user_order, product_offer,
        proposed_to_user_product_offer, proposed_to_user_product_offer_2):
    wine_expert_email = wine_expert.email
    proposed_to_user_order_id = proposed_to_user_order.id

    class Customer:
        id = user.stripe_customer_id

    class Charge:
        id = 'charge_id'

    stripe_m.Customer.retrieve.return_value = Customer

    stripe_m.Charge.create.return_value = Charge

    global_offer_id = graphene.Node.to_global_id(
        proposed_to_user_product_offer.__class__.__name__,
        proposed_to_user_product_offer.id
    )

    query = """mutation acceptOffer($input: AcceptProductOfferInput!) {
        acceptOffer(input: $input) { clientMutationId }
    }
    """
    variables = {
        'input': {
            'offerId': global_offer_id,
        }}

    # Test
    graphql_client.post(query, variables)

    # Check
    offer = db.session.query(ProductOffer).filter_by(id=proposed_to_user_product_offer.id).first()
    order = offer.order

    assert offer.stripe_charge_id == Charge.id
    stripe_m.Customer.retrieve.assert_called_once_with(user.stripe_customer_id)
    stripe_m.Charge.create.assert_called_once_with(
        amount=int(offer.total_cost * 100),
        currency='usd',
        customer=Customer.id,
        capture=False
    )
    order_url = get_admin_order_url(proposed_to_user_order_id)
    send_mail_m.assert_called_once_with(
        wine_expert_email,
        'Accepted Order',
        "User has accepted Product Offer: %s in Order: %s. It's available here: %s" %
        (proposed_to_user_product_offer.id, proposed_to_user_order_id, order_url)
    )

    assert order.state == SUPPORT_NOTIFIED_STATE
