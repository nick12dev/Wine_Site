#
# pylint: disable=unused-argument,bad-continuation
from datetime import datetime
from unittest.mock import patch


def test_order_history_against_nonhistory(
        graphql_client, proposed_to_user_offer_item, accepted_order, completed_orders
):
    query = """
        {
          user {
            orderHistory {
              edges {
                node {
                  user {
                    firstName
                  }
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
                  orderTime
                  createdAt
                  stateChangedAt
                  acceptedOffer {
                    name
                    wineType
                    bottleQty
                    expertNote
                    priority
                    accepted
                    productCost
                    salestaxCost
                    shippingCost
                    totalCost
                    order {
                        state
                    }
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
                          highlights}}}}}}}}}
    """

    res = graphql_client.post(query)

    expected = {'data': {'user': {'orderHistory': {'edges':
        [
            {'node': {
                'createdAt': f'{2000 + i}-10-10T12:02:38.784862',
                'stateChangedAt': f'{2010 + i}-10-10T12:02:38.784862',
                'orderTime': f'{2010 + i}-10-10T12:02:38.784862',
                'acceptedOffer': {
                    'accepted': True,
                    'bottleQty': 2,
                    'expertNote': None,
                    'name': 'source_1',
                    'order': {
                        'state': 'completed',
                    },
                    'offerItems': {'edges': [
                        {'node': {'brand': 'brand',
                                  'description': 'Short description',
                                  'highlights': ['Highlights'],
                                  'varietals': ['Varietals'],
                                  'msrp': '3.99',
                                  'sku': '123',
                                  'qoh': 1,
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
                                  'description': 'Short description',
                                  'highlights': ['Highlights'],
                                  'varietals': ['Varietals'],
                                  'msrp': '3.99',
                                  'sku': '123',
                                  'qoh': 1,
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
                                  'description': 'Short description',
                                  'highlights': ['Highlights'],
                                  'varietals': ['Varietals'],
                                  'msrp': '3.99',
                                  'sku': '123',
                                  'qoh': 1,
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
                                  'scoreNum': 101}}
                    ]},
                    'priority': 11,
                    'productCost': None,
                    'salestaxCost': None,
                    'shippingCost': None,
                    'totalCost': '98.00',
                    'wineType': 'mixed'},
                'shippingCity': 'New York',
                'shippingCountry': 'US',
                'shippingName': 'tuser' + str(i),
                'shippingPhone': None,
                'shippingPostcode': '1234',
                'shippingStateRegion': 'New York',
                'shippingStreet1': 'street 1',
                'shippingStreet2': None,
                'shippingTrackingNum': None,
                'state': 'completed',
                'user': {'firstName': 'tuser'}}}

            for i in range(3, -1, -1)
        ]
    }}}}

    assert res == expected


def test_upcoming_order_against_other_orders(
        graphql_client, proposed_to_user_offer_item, accepted_order, completed_orders
):
    query = """
        {
          user {
            upcomingOrder {
              user {
                firstName
              }
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
              acceptedOffer {
                name
                wineType
                bottleQty
                expertNote
                priority
                accepted
                productCost
                salestaxCost
                shippingCost
                totalCost
                order {
                    state
                }
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
                      highlights}}}}}}}
    """

    res = graphql_client.post(query)

    expected = {'data': {'user': {'upcomingOrder': {
        'acceptedOffer': {
            'accepted': True,
            'bottleQty': 2,
            'expertNote': None,
            'name': 'source_1',
            'order': {
                'state': 'offer_accepted',
            },
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
                          'scoreNum': 101}}
            ]},
            'priority': 11,
            'productCost': None,
            'salestaxCost': None,
            'shippingCost': None,
            'totalCost': '98.00',
            'wineType': 'mixed'
        },
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
        'user': {'firstName': 'tuser'}}}}}

    assert res == expected


def test_proposed_order_against_other_orders(
        graphql_client, proposed_to_user_offer_item, accepted_order, completed_orders
):
    query = """
        {
          user {
            proposedOrder {
              user {
                firstName
              }
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
              productOffers {
                edges {
                    node {
                        name
                        wineType
                        bottleQty
                        expertNote
                        priority
                        accepted
                        productCost
                        salestaxCost
                        shippingCost
                        totalCost
                        order {
                            state
                        }
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
                              highlights}}}}}}}}}
    """

    res = graphql_client.post(query)

    expected = {'data': {'user': {'proposedOrder': {'productOffers': {'edges': [
        {'node': {'accepted': False,
                  'bottleQty': 3,
                  'expertNote': None,
                  'name': 'source_1',
                  'order': {
                      'state': 'proposed_to_user',
                  },
                  'offerItems': {'edges': [{'node': {'brand': 'brand',
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
                                                             'name',
                                                     'price': '80.00',
                                                     'qty': None,
                                                     'scoreNum': 99}}]},
                  'priority': 0,
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
        'user': {'firstName': 'tuser'}}}}}

    assert res == expected


def test_order_is_active_true(
        graphql_client, completed_orders, proposed_to_user_order
):
    query = """
        {
          user {
            userSubscription {
              orderIsActive
            }
            proposedOrder {
              isInProcess
            }
          }
        }
    """

    # Test
    res = graphql_client.post(query)

    # Check
    assert res == {'data': {
        'user': {
            'userSubscription': {'orderIsActive': True},
            'proposedOrder': {'isInProcess': True}
        }
    }}


def test_order_is_active_false(
        graphql_client, completed_orders, accepted_order
):
    query = """
        {
          user {
            userSubscription {
              orderIsActive
            }
          }
        }
    """

    res = graphql_client.post(query)

    # Check
    assert res == {'data': {'user': {'userSubscription': {'orderIsActive': False}}}}


order_month_query = """
    {
      user {
        userSubscription {
          orderIsActive
          orderIsInProcess
          orderMonthTime
          monthToProcess
        }
      }
    }
"""


@patch('core.graphql.schemas.user_subscription.datetime')
@patch('core.db.models.order.datetime')
def test_order_is_in_process_true(
        datetime_m1, datetime_m2, graphql_client, completed_orders, order_20150515
):
    datetime_m1.utcnow.return_value = datetime(2015, 5, 25, 1, 1, 1, 1)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect

    # Test
    res = graphql_client.post(order_month_query)

    # Check
    assert res == {'data': {'user': {'userSubscription': {
        'orderIsActive': True,
        'orderIsInProcess': True,
        'orderMonthTime': '2015-05-15T13:13:13.000013',
        'monthToProcess': 5,
    }}}}


@patch('core.graphql.schemas.user_subscription.datetime')
@patch('core.db.models.order.datetime')
def test_order_is_in_process_false(
        datetime_m1, datetime_m2, graphql_client, completed_orders, order_20150515
):
    datetime_m1.utcnow.return_value = datetime(2015, 5, 5, 1, 1, 1, 1)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect

    # Test
    res = graphql_client.post(order_month_query)

    # Check
    assert res == {'data': {'user': {'userSubscription': {
        'orderIsActive': True,
        'orderIsInProcess': False,
        'orderMonthTime': '2015-05-15T13:13:13.000013',
        'monthToProcess': 5,
    }}}}


@patch('core.graphql.schemas.user_subscription.datetime')
@patch('core.db.models.order.datetime')
def test_exception_to_notify_order_is_in_process_false(
        datetime_m1, datetime_m2, graphql_client, exception_to_notify_order_20150515
):
    datetime_m1.utcnow.return_value = datetime(2015, 5, 25, 1, 1, 1, 1)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect

    # Test
    res = graphql_client.post(order_month_query)

    # Check
    assert res == {'data': {'user': {'userSubscription': {
        'orderIsActive': False,
        'orderIsInProcess': False,
        'orderMonthTime': '2015-05-15T13:13:13.000013',
        'monthToProcess': 5,
    }}}}


@patch('core.graphql.schemas.user_subscription.datetime')
@patch('core.db.models.order.datetime')
def test_exception_order_is_in_process_false(
        datetime_m1, datetime_m2, graphql_client, exception_order_20150515
):
    datetime_m1.utcnow.return_value = datetime(2015, 6, 15, 1, 1, 1, 1)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect

    # Test
    res = graphql_client.post(order_month_query)

    # Check
    assert res == {'data': {'user': {'userSubscription': {
        'orderIsActive': False,
        'orderIsInProcess': False,
        'orderMonthTime': '2015-05-15T13:13:13.000013',
        'monthToProcess': 5,
    }}}}
