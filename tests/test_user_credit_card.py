# pylint: disable=too-many-arguments,unused-argument
from unittest.mock import patch, MagicMock

from stripe.error import StripeError

from core.dbmethods.user import (
    get_user,
    save_stripe_customer_id,
)


@patch('core.dbmethods.user.stripe')
def test_save_stripe_customer(stripe_m, graphql_client3, user_no_stripe):
    user_id = user_no_stripe.id
    customer = MagicMock()
    customer.id = 'customer_id'

    stripe_m.Customer.create.return_value = customer
    token = 'stripe_token'

    query = """
        mutation saveUser ($input: SaveUserInput!) 
         { saveUser(input: $input) {clientMutationId} } 
    """
    variables = {
        'input': {
            'clientMutationId': 'test_id',
            'firstName': 'new_test_name',
            'stripeToken': token
        }
    }

    # Test
    graphql_client3.post(query, variables)

    # Check
    _user = get_user(user_id)
    assert _user.stripe_customer_id == customer.id
    stripe_m.Customer.create.assert_called_once_with(
        source=token, email=user_no_stripe.email
    )


@patch('core.dbmethods.user.stripe')
def test_save_stripe_customer_unknown_error(stripe_m, graphql_client3, user_no_stripe):
    user_email = user_no_stripe.email
    customer = MagicMock()
    customer.id = 'customer_id'

    stripe_m.Customer.create.side_effect = Exception('stripe error!')
    token = 'stripe_token'

    query = """
        mutation saveUser ($input: SaveUserInput!) 
         { saveUser(input: $input) {clientMutationId} } 
    """
    variables = {
        'input': {
            'clientMutationId': 'test_id',
            'firstName': 'new_test_name',
            'stripeToken': token
        }
    }

    # Test
    res = graphql_client3.post(query, variables)

    # Check
    stripe_m.Customer.create.assert_called_once_with(
        source=token, email=user_email
    )
    assert res['errors'][0]['message'] == 'Unknown error when saving Stripe Customer'


@patch('core.dbmethods.user.stripe')
def test_save_stripe_customer_stripe_error(stripe_m, graphql_client3, user_no_stripe):
    user_email = user_no_stripe.email
    customer = MagicMock()
    customer.id = 'customer_id'

    stripe_m.Customer.create.side_effect = StripeError('stripe error!', code='error_code')
    token = 'stripe_token'

    query = """
        mutation saveUser ($input: SaveUserInput!) 
         { saveUser(input: $input) {clientMutationId} } 
    """
    variables = {
        'input': {
            'clientMutationId': 'test_id',
            'firstName': 'new_test_name',
            'stripeToken': token
        }
    }

    # Test
    res = graphql_client3.post(query, variables)

    # Check
    stripe_m.Customer.create.assert_called_once_with(
        source=token, email=user_email
    )
    assert res['errors'][0]['message'] == 'stripe error!'


@patch('core.dbmethods.user.stripe')
def test_update_stripe_customer(stripe_m, graphql_client, user):
    user_id = user.id
    customer = MagicMock()
    customer.id = user.stripe_customer_id

    stripe_m.Customer.retrieve.return_value = customer
    token = 'stripe_token'

    query = """
        mutation saveUser ($input: SaveUserInput!)
         { saveUser(input: $input) {clientMutationId} }
    """
    variables = {
        'input': {
            'clientMutationId': 'test_id',
            'firstName': 'new_test_name',
            'stripeToken': token
        }
    }

    # Test
    graphql_client.post(query, variables)

    # Check
    _user = get_user(user_id)
    assert _user.stripe_customer_id == customer.id
    stripe_m.Customer.retrieve.assert_called_once_with(customer.id)
    stripe_m.Customer.modify.assert_called_once_with(customer.id, source=token)


@patch('core.dbmethods.user.stripe')
def test_save_stripe_customer_id(stripe_m, app, user_no_stripe):
    customer = MagicMock()
    customer.id = 'customer_id'

    stripe_m.Customer.create.return_value = customer

    # Test
    token = 'test_token'
    save_stripe_customer_id(user_no_stripe.id, token)

    # Check
    _user = get_user(user_no_stripe.id)
    assert _user.stripe_customer_id == customer.id
    stripe_m.Customer.create.assert_called_once_with(
        source=token, email=user_no_stripe.email
    )


@patch('core.dbmethods.user.stripe')
def test_get_credit_card(stripe_m, graphql_client, user):
    class CreditCard:
        brand = 'Visa'
        country = 'US'
        exp_month = '12'
        exp_year = '2019'
        last4 = '1111'
        name = 'card holder'

    customer = MagicMock()
    customer.sources.data = [CreditCard]

    stripe_m.Customer.retrieve.return_value = customer
    query = """
        { user
          { creditCard {
            brand
            country
            expMonth
            expYear
            last4
            name}}}
    """

    # Test
    res = graphql_client.post(query)

    # Check
    stripe_m.Customer.retrieve.assert_called_once_with('stripe_customer_id')

    expected = {
        'data': {
            'user': {
                'creditCard': {
                    'brand': 'Visa', 'country': 'US',
                    'expMonth': '12', 'expYear': '2019',
                    'last4': '1111', 'name': 'card holder'
                },
            }
        }
    }
    assert res == expected
