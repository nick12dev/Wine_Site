# pylint: disable=unused-argument,bad-continuation
import datetime
from unittest.mock import (
    patch,
    MagicMock,
)

from graphene import Node

from core.db.models import (
    PLACE_ORDER_ACTION,
    ORDER_PLACED_STATE,
    SET_SHIPPED_ACTION,
    USER_NOTIFIED_SHIPPED_STATE,
    SET_USER_RECEIVED_ACTION,
)
from core.db.models.order import Order
from core.order.order_manager import run_order

order_list_query = '''
    query ($offset: Int, $first: Int, $sort: OrderSortEnum, $listFilter: OrderFilter) {
      orderManagement {
        orders(offset: $offset, first: $first, sort: $sort, listFilter: $listFilter) {
          totalCount
          edges {
            node {
              state
              shippingName
              shippingCity
              user {
                firstName}}}}}}
'''


def test_order_list_nonadmin(
        graphql_client, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client.post(order_list_query)
    assert res['data']['orderManagement'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']


expected_order_list_sorted_by_state_changed_at_desc = {
    'data': {'orderManagement': {'orders': {'edges': [
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser3',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser2',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser1',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser0',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}}],
        'totalCount': 4}}}}


def test_order_list_default_sort(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client_admin.post(order_list_query, variables={
        'listFilter': {
            'orderNumber': '',
            'state': 'completed',
            'user': 'usE'
        }
    })
    assert res == expected_order_list_sorted_by_state_changed_at_desc


def test_order_list_sort_by_state_changed_at_desc(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client_admin.post(order_list_query, variables={
        'sort': 'state_changed_at_desc',
        'listFilter': {
            'orderNumber': '',
            'state': 'completed',
            'user': 'usE'
        }
    })
    assert res == expected_order_list_sorted_by_state_changed_at_desc


def test_order_list_sort_by_order_time_desc(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client_admin.post(order_list_query, variables={
        'sort': 'order_time_desc',
        'listFilter': {
            'orderNumber': '',
            'state': 'completed',
            'user': 'usE'
        }
    })
    assert res == expected_order_list_sorted_by_state_changed_at_desc


def test_order_list_sort_by_number_desc(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client_admin.post(order_list_query, variables={
        'offset': 1,
        'first': 2,
        'sort': 'order_number_desc',
        'listFilter': {
            'orderNumber': '',
            'state': 'completed',
            'user': 'usE'
        }
    })

    expected = {'data': {'orderManagement': {'orders': {'edges': [
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser2',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser1',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
    ], 'totalCount': 4}}}}

    assert res == expected


def test_order_list_sort_by_user_asc(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders, order2
):
    res = graphql_client_admin.post(order_list_query, variables={
        'offset': 2,
        'first': 3,
        'sort': 'user_display_name_asc',
        'listFilter': {
            'user': 'use'
        }
    })

    expected = {'data': {'orderManagement': {'orders': {'edges': [
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser0',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser1',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser2',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
    ], 'totalCount': 7}}}}

    assert res == expected


def test_order_list_sort_by_user_desc(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders, order2
):
    res = graphql_client_admin.post(order_list_query, variables={
        'first': 3,
        'sort': 'user_display_name_desc',
    })

    expected = {'data': {'orderManagement': {'orders': {'edges': [
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser2',
                  'state': 'started',
                  'user': {'firstName': 'tuser2'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser3',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
        {'node': {'shippingCity': 'New '
                                  'York',
                  'shippingName': 'tuser2',
                  'state': 'completed',
                  'user': {'firstName': 'tuser'}}},
    ], 'totalCount': 7}}}}

    assert res == expected


def test_order_states_for_filtering(graphql_client_admin):
    query = '''
        { orderManagement { orderStates } }
    '''

    res = graphql_client_admin.post(query)

    expected = {'data': {'orderManagement': {'orderStates': [
        'started',
        'ready_to_propose',
        'proposed_to_wine_expert',
        'approved_by_expert',
        'proposed_to_user',
        'offer_accepted',
        'support_notified_accepted_offer',
        'order_placed',
        'order_shipped',
        'money_captured',
        'user_notified_shipped',
        'user_received',
        'completed',
        'exception_to_notify',
        'exception',
        'search_exception_to_notify',
        'search_exception',
        'notify_wine_expert_exception_to_notify',
        'notify_wine_expert_exception',
        'authorize_payment_exception_to_notify',
        'authorize_payment_exception',
        'notify_accepted_offer_exception_to_notify',
        'notify_accepted_offer_exception',
        'capture_money_exception_to_notify',
        'capture_money_exception',
        'next_month_order_exception_to_notify',
        'next_month_order_exception']}}}

    assert res == expected


def test_order_shipping_methods(
        app, graphql_client_admin, order_shipping_method_1, order_shipping_method_2, order_shipping_method_3
):
    query = '''
        { orderManagement { shippingMethods {
            id
            name}}}
    '''

    osm_id1 = order_shipping_method_1.id
    osm_id2 = order_shipping_method_2.id
    osm_id3 = order_shipping_method_3.id

    res = graphql_client_admin.post(query)

    expected = {'data': {'orderManagement': {'shippingMethods': [
        {
            'id': Node.to_global_id('OrderShippingMethod', osm_id3),
            'name': 'FedEx Ground'
        },
        {
            'id': Node.to_global_id('OrderShippingMethod', osm_id1),
            'name': 'GSO Ground'
        },
        {
            'id': Node.to_global_id('OrderShippingMethod', osm_id2),
            'name': 'UPS Ground'
        },
    ]}}}

    assert res == expected


order_details_query = '''
    query($id: ID!) {
      node(id: $id) {
        ... on Order {
          state
          shippingName
          shippingStreet1
          shippingStreet2
          shippingStateRegion
          shippingCountry
          shippingCity
          shippingPostcode
          shippingPhone
          shippingTrackingNum
          user {
            firstName
          }
          subscription {
            bottleQty
            type
            budget
          }
          subscriptionSnapshot {
            edges {
              node {
                bottleQty
                type
                budget
              }
            }
          }
          singleOffer {
            name
            offerItems {
              edges {
                node {
                  name
                }
              }
            }
          }
          productOffers {
            edges {
              node {
                name
                wineType
                bottleQty
                expertNote
                priority
                accepted
                offerItems {
                  edges {
                    node {
                      name
                      scoreNum
                      image
                      description
                      location
                      qty
                      brand
                      price
                      bestTheme {
                        title
                        shortDescription
                        image
                      }
                      varietals
                      highlights
                      qoh
                      sku
                      msrp
                      productUrl
                    }
                  }
                }
                productCost
                salestaxCost
                shippingCost
                totalCost
              }
            }
          }
          allowedActions
          acceptedOffer {
            name}}}}
'''


def test_order_details_nonadmin(
        graphql_client, proposed_to_user_offer_item, accepted_order, completed_orders, order2
):
    res = graphql_client.post(order_details_query, variables={
        'id': Node.to_global_id('Order', order2.id)
    })

    assert res['data']['node'] is None


def test_order_details(
        graphql_client_admin, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client_admin.post(order_details_query, variables={
        'id': Node.to_global_id('Order', accepted_order.id)
    })

    expected = {'data': {'node': {
        'acceptedOffer': {'name': 'source_1'},
        'allowedActions': [],
        'singleOffer': {
            'name': 'source_1',
            'offerItems': {'edges': [
                {'node': {'name': 'wine name0'}},
                {'node': {'name': 'wine name1'}},
                {'node': {'name': 'wine name2'}}]}},
        'productOffers': {'edges': [
            {'node': {'accepted': True,
                      'bottleQty': 2,
                      'expertNote': None,
                      'name': 'source_1',
                      'offerItems': {
                          'edges': [{'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'msrp': '3.99',
                                              'name': 'wine '
                                                      'name0',
                                              'price': '81.00',
                                              'productUrl': 'http://product',
                                              'qoh': 1,
                                              'qty': None,
                                              'scoreNum': 99,
                                              'sku': '123'}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'msrp': '3.99',
                                              'name': 'wine '
                                                      'name1',
                                              'price': '81.00',
                                              'productUrl': 'http://product',
                                              'qoh': 1,
                                              'qty': None,
                                              'scoreNum': 100,
                                              'sku': '123'}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'msrp': '3.99',
                                              'name': 'wine '
                                                      'name2',
                                              'price': '81.00',
                                              'productUrl': 'http://product',
                                              'qoh': 1,
                                              'qty': None,
                                              'scoreNum': 101,
                                              'sku': '123'}}]},
                      'priority': 11,
                      'productCost': None,
                      'salestaxCost': None,
                      'shippingCost': None,
                      'totalCost': '98.00',
                      'wineType': 'mixed'}},
            {'node': {'accepted': False,
                      'bottleQty': 3,
                      'expertNote': None,
                      'name': 'source_1',
                      'offerItems': {
                          'edges': [{'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'msrp': '3.99',
                                              'name': 'wine '
                                                      'name0',
                                              'price': '81.00',
                                              'productUrl': 'http://product',
                                              'qoh': 1,
                                              'qty': None,
                                              'scoreNum': 99,
                                              'sku': '123'}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'msrp': '3.99',
                                              'name': 'wine '
                                                      'name1',
                                              'price': '81.00',
                                              'productUrl': 'http://product',
                                              'qoh': 1,
                                              'qty': None,
                                              'scoreNum': 100,
                                              'sku': '123'}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'msrp': '3.99',
                                              'name': 'wine '
                                                      'name2',
                                              'price': '81.00',
                                              'productUrl': 'http://product',
                                              'qoh': 1,
                                              'qty': None,
                                              'scoreNum': 101,
                                              'sku': '123'}}]},
                      'priority': 10,
                      'productCost': None,
                      'salestaxCost': None,
                      'shippingCost': None,
                      'totalCost': '99.00',
                      'wineType': 'mixed'}}]},
        'shippingCity': 'New York',
        'shippingCountry': 'US',
        'shippingName': 'tuser',
        'shippingPhone': None,
        'shippingPostcode': '1234',
        'shippingStateRegion': 'New York',
        'shippingStreet1': 'street 1',
        'shippingStreet2': None,
        'shippingTrackingNum': None,
        'state': 'offer_accepted',
        'subscription': {'bottleQty': None,
                         'budget': None,
                         'type': 'mixed'},
        'subscriptionSnapshot': {
            'edges': [
                {'node': {'bottleQty': None,
                          'budget': None,
                          'type': 'mixed'}},
            ],
        },
        'user': {'firstName': 'tuser'}}}}

    assert res == expected


def _run_order_task_mock(*args, **kwargs):
    run_order(*args, **kwargs)
    return MagicMock()


@patch('core.graphql.schemas.order.run_order')
@patch('core.order.actions.user.boto3')
@patch('core.order.actions.support_admin.send_mail')
@patch('core.order.actions.user.send_template_email')
def test_order_run_action(
        send_user_mail_m, send_mail_m, boto_m, run_order_m,
        graphql_client_admin, proposed_to_wine_expert_order,
):
    run_order_m.delay.side_effect = _run_order_task_mock

    query = '''
        mutation($input: SaveOrderInput!) {
          saveOrder(input: $input) {
            clientMutationId
            order {
              state
              shippingName
              shippingStreet1
              shippingStreet2
              shippingStateRegion
              shippingCountry
              shippingCity
              shippingPostcode
              shippingPhone
              shippingTrackingNum
              user {
                firstName
              }
              subscription {
                bottleQty
                type
                budget
              }
              productOffers {
                edges {
                  node {
                    name
                    wineType
                    bottleQty
                    expertNote
                    priority
                    accepted
                    offerItems {
                      edges {
                        node {
                          name
                          scoreNum
                          image
                          description
                          location
                          qty
                          brand
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
                          varietals
                          highlights
                        }
                      }
                    }
                    productCost
                    salestaxCost
                    shippingCost
                    totalCost
                  }
                }
              }
              allowedActions
              acceptedOffer {
                name}}}}
    '''

    res = graphql_client_admin.post(query, variables={
        'input': {
            'id': Node.to_global_id('Order', proposed_to_wine_expert_order.id),
            'action': 'approve',
            'clientMutationId': 'test'
        }
    })

    expected = {'data': {'saveOrder': {
        'clientMutationId': 'test',
        'order': {'acceptedOffer': {'name': 'source_1'},
                  'allowedActions': ['retry_search'],
                  'productOffers': {'edges': [
                      {'node': {'accepted': True,
                                'bottleQty': 2,
                                'expertNote': None,
                                'name': 'source_1',
                                'offerItems': {'edges': [
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'sku': '123',
                                              'qoh': 1,
                                              'msrp': '3.99',
                                              'productUrl': 'http://product',
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'name': 'wine '
                                                      'name0',
                                              'price': '81.00',
                                              'qty': None,
                                              'scoreNum': 99}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'sku': '123',
                                              'qoh': 1,
                                              'msrp': '3.99',
                                              'productUrl': 'http://product',
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'name': 'wine '
                                                      'name1',
                                              'price': '81.00',
                                              'qty': None,
                                              'scoreNum': 100}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'sku': '123',
                                              'qoh': 1,
                                              'msrp': '3.99',
                                              'productUrl': 'http://product',
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'name': 'wine '
                                                      'name2',
                                              'price': '81.00',
                                              'qty': None,
                                              'scoreNum': 101}}]},
                                'priority': 11,
                                'productCost': None,
                                'salestaxCost': None,
                                'shippingCost': None,
                                'totalCost': '98.00',
                                'wineType': 'mixed'}},
                      {'node': {'accepted': False,
                                'bottleQty': 3,
                                'expertNote': None,
                                'name': 'source_1',
                                'offerItems': {'edges': [
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'sku': '123',
                                              'qoh': 1,
                                              'msrp': '3.99',
                                              'productUrl': 'http://product',
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'name': 'wine '
                                                      'name0',
                                              'price': '81.00',
                                              'qty': None,
                                              'scoreNum': 99}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'sku': '123',
                                              'qoh': 1,
                                              'msrp': '3.99',
                                              'productUrl': 'http://product',
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'name': 'wine '
                                                      'name1',
                                              'price': '81.00',
                                              'qty': None,
                                              'scoreNum': 100}},
                                    {'node': {'brand': 'brand',
                                              'description': 'Short '
                                                             'description',
                                              'highlights': ['Highlights'],
                                              'varietals': ['Varietals'],
                                              'sku': '123',
                                              'qoh': 1,
                                              'msrp': '3.99',
                                              'productUrl': 'http://product',
                                              'bestTheme': {
                                                  'title': 'theme 1',
                                                  'shortDescription': 'theme short desc 1',
                                                  'image': 'https://someimage.url',
                                              },
                                              'image': 'img_url',
                                              'location': 'Region',
                                              'name': 'wine '
                                                      'name2',
                                              'price': '81.00',
                                              'qty': None,
                                              'scoreNum': 101}}]},
                                'priority': 10,
                                'productCost': None,
                                'salestaxCost': None,
                                'shippingCost': None,
                                'totalCost': '99.00',
                                'wineType': 'mixed'}}]},
                  'shippingCity': 'New York',
                  'shippingCountry': 'US',
                  'shippingName': 'tuser',
                  'shippingPhone': None,
                  'shippingPostcode': '1234',
                  'shippingStateRegion': 'New York',
                  'shippingStreet1': 'street 1',
                  'shippingStreet2': None,
                  'shippingTrackingNum': None,
                  'state': 'proposed_to_user',
                  'subscription': {'bottleQty': None,
                                   'budget': None,
                                   'type': 'mixed'},
                  'user': {'firstName': 'tuser'}}}}}

    assert res == expected

    modified_order = Order.query.get(proposed_to_wine_expert_order.id)
    assert modified_order.state == 'proposed_to_user'
    send_user_mail_m.assert_called_once()


def test_order_edit(
        graphql_client_admin, support_notified_order, order_shipping_method_2,
        support_notified_product_offer, support_notified_offer_item_1, support_notified_offer_item_2
):
    query = '''
        mutation ($input: SaveOrderInput!) {
          saveOrder(input: $input) {
            clientMutationId
            order {
              state
              allowedActions
              shippingName
              shippingStreet1
              shippingStreet2
              shippingCity
              shippingCountry
              shippingStateRegion
              shippingPostcode
              shippingPhone
              shippingTrackingNum
              shippingDate
              shippingMethod {
                id
                name
              }
              shippingTrackingUrl
              productOffers {
                  edges {
                    node {
                        productCost
                        salestaxCost
                        shippingCost
                        totalCost
                        expertNote
                    }}}}}}
    '''

    osm_id = Node.to_global_id('OrderShippingMethod', order_shipping_method_2.id)

    # Test
    res = graphql_client_admin.post(query, variables={
        'input': {
            'id': Node.to_global_id('Order', support_notified_order.id),
            'clientMutationId': 'test',
            'shippingName': 'test name 55',
            'shippingStreet1': 'test street 551',
            'shippingStreet2': 'test street 552',
            'shippingCity': 'test city 55',
            'shippingCountry': 'test country 55',
            'shippingStateRegion': 'test state region 55',
            'shippingPostcode': '55355',
            'shippingPhone': '+15513551355',
            'shippingTrackingNum': '1313551313551313',
            'shippingDate': '2015-09-15',
            'shippingMethodId': osm_id,
            'productOffers': [
                {
                    'id': Node.to_global_id('ProductOffer', support_notified_product_offer.id),
                    'expertNote': 'test expert note 1',
                    'salestaxCost': '3.13',
                    'shippingCost': '4.12',
                },
            ], }, })

    # Check
    expected = {
        'data': {
            'saveOrder': {
                'clientMutationId': 'test',
                'order': {
                    'state': 'support_notified_accepted_offer',
                    'allowedActions': ['place_order'],
                    'shippingName': 'test name 55',
                    'shippingStreet1': 'test street 551',
                    'shippingStreet2': 'test street 552',
                    'shippingCity': 'test city 55',
                    'shippingCountry': 'test country 55',
                    'shippingStateRegion': 'test state region 55',
                    'shippingPostcode': '55355',
                    'shippingPhone': '+15513551355',
                    'shippingTrackingNum': '1313551313551313',
                    'shippingDate': '2015-09-15',
                    'shippingMethod': {
                        'id': osm_id,
                        'name': 'UPS Ground',
                    },
                    'shippingTrackingUrl': 'http://wwwapps.ups.com/WebTracking/track?track=yes&trackNums=1313551313551313',
                    'productOffers': {
                        'edges': [
                            {
                                'node': {
                                    'productCost': '130.00',
                                    'salestaxCost': '3.13',
                                    'shippingCost': '4.12',
                                    'totalCost': '137.25',
                                    'expertNote': 'test expert note 1'
                                },
                            },
                        ], }, }, }, }, }
    assert res == expected

    modified_order = Order.query.get(support_notified_order.id)
    assert modified_order.state == 'support_notified_accepted_offer'
    assert modified_order.shipping_name == 'test name 55'
    assert modified_order.shipping_street1 == 'test street 551'
    assert modified_order.shipping_street2 == 'test street 552'
    assert modified_order.shipping_city == 'test city 55'
    assert modified_order.shipping_country == 'test country 55'
    assert modified_order.shipping_state_region == 'test state region 55'
    assert modified_order.shipping_postcode == '55355'
    assert modified_order.shipping_phone == '+15513551355'
    assert modified_order.shipping_tracking_num == '1313551313551313'
    assert modified_order.shipping_date == datetime.date(2015, 9, 15)


@patch('core.graphql.schemas.order.run_order')
def test_run_place_order_action_with_edit(
        run_order_m, graphql_client_admin, support_notified_order, support_notified_product_offer
):
    run_order_m.delay.side_effect = _run_order_task_mock

    query = '''
        mutation ($input: SaveOrderInput!) {
          saveOrder(input: $input) {
            clientMutationId
            order {
              state
              allowedActions
              shippingName
              shippingStreet1
              shippingStreet2
              shippingCity
              shippingCountry
              shippingStateRegion
              shippingPostcode
              shippingPhone
              shippingTrackingNum
              shippingDate}}}
    '''

    # Test
    res = graphql_client_admin.post(query, variables={
        'input': {
            'id': Node.to_global_id('Order', support_notified_order.id),
            'action': PLACE_ORDER_ACTION,
            'clientMutationId': 'test',
            'shippingName': 'test name 55',
            'shippingStreet1': 'test street 551',
            'shippingStreet2': 'test street 552',
            'shippingCity': 'test city 55',
            'shippingCountry': 'test country 55',
            'shippingStateRegion': 'test state region 55',
            'shippingPostcode': '55355',
            'shippingPhone': '+15513551355',
            'shippingTrackingNum': '1313551313551313',
            'shippingDate': '2020-11-29',
        }
    })

    # Check
    expected = {
        'data': {
            'saveOrder': {
                'clientMutationId': 'test',
                'order': {
                    'state': ORDER_PLACED_STATE,
                    'allowedActions': [SET_SHIPPED_ACTION],
                    'shippingName': 'test name 55',
                    'shippingStreet1': 'test street 551',
                    'shippingStreet2': 'test street 552',
                    'shippingCity': 'test city 55',
                    'shippingCountry': 'test country 55',
                    'shippingStateRegion': 'test state region 55',
                    'shippingPostcode': '55355',
                    'shippingPhone': '+15513551355',
                    'shippingTrackingNum': '1313551313551313',
                    'shippingDate': '2020-11-29',
                }
            }
        }
    }
    assert res == expected

    modified_order = Order.query.get(support_notified_order.id)
    assert modified_order.state == ORDER_PLACED_STATE
    assert modified_order.shipping_name == 'test name 55'
    assert modified_order.shipping_street1 == 'test street 551'
    assert modified_order.shipping_street2 == 'test street 552'
    assert modified_order.shipping_city == 'test city 55'
    assert modified_order.shipping_country == 'test country 55'
    assert modified_order.shipping_state_region == 'test state region 55'
    assert modified_order.shipping_postcode == '55355'
    assert modified_order.shipping_phone == '+15513551355'
    assert modified_order.shipping_tracking_num == '1313551313551313'
    assert modified_order.shipping_date == datetime.date(2020, 11, 29)


@patch('core.graphql.schemas.order.run_order')
@patch('core.dbmethods.user.stripe')
@patch('core.order.actions.user.send_template_email')
def test_run_set_shipped_action(
        send_mail_m, stripe_m, run_order_m,
        graphql_client_admin, placed_order, placed_product_offer,
):
    run_order_m.delay.side_effect = _run_order_task_mock

    query = '''
        mutation($input: SaveOrderInput!) {
          saveOrder(input: $input) {
            clientMutationId
            order {
              state
              allowedActions}}}
    '''

    # Test
    res = graphql_client_admin.post(query, variables={
        'input': {
            'id': Node.to_global_id('Order', placed_order.id),
            'action': SET_SHIPPED_ACTION,
            'clientMutationId': 'test'
        }
    })

    # Check
    expected = {
        'data': {
            'saveOrder': {
                'clientMutationId': 'test',
                'order': {
                    'state': USER_NOTIFIED_SHIPPED_STATE, 'allowedActions': [SET_USER_RECEIVED_ACTION]
                }
            }
        }
    }
    assert res == expected

    modified_order = Order.query.get(placed_order.id)
    assert modified_order.state == USER_NOTIFIED_SHIPPED_STATE
    send_mail_m.assert_called_once()


def test_order_run_action_nonadmin(graphql_client, accepted_order):
    query = '''
        mutation($input: SaveOrderInput!) {
          saveOrder(input: $input) {
            clientMutationId
          }
        }
    '''

    res = graphql_client.post(query, variables={
        'input': {
            'id': Node.to_global_id('Order', accepted_order.id),
            'action': 'notify_accepted_offer',
            'clientMutationId': 'test'
        }
    })

    assert res['data']['saveOrder'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']

    modified_order = Order.query.get(accepted_order.id)
    assert modified_order.action is None
