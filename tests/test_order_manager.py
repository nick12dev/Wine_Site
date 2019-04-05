# pylint: disable=unused-argument,no-member,too-many-arguments
import json
from unittest.mock import (
    patch,
    MagicMock,
)
from datetime import datetime

from core.db.models import (
    db,
    READY_TO_PROPOSE_STATE,
    PROPOSED_TO_WINE_EXPERT_STATE,
    PROPOSED_TO_USER_STATE,
    APPROVE_ACTION,
    STARTED_STATE,
    SET_SHIPPED_ACTION,
    USER_NOTIFIED_SHIPPED_STATE,
    ORDER_PLACED_STATE,
    PLACE_ORDER_ACTION,
    ORDER_SHIPPED_STATE,
    MONEY_CAPTURED_STATE,
    SET_USER_RECEIVED_ACTION,
    COMPLETED_STATE,
    USER_RECEIVED_STATE,
    SUBSCRIPTION_SUSPENDED_STATE,
    NOTIFY_WINE_EXPERT_EXCEPTION_TO_NOTIFY_STATE,
    NOTIFY_WINE_EXPERT_EXCEPTION_STATE,
    SEARCH_EXCEPTION_TO_NOTIFY_STATE,
    SEARCH_EXCEPTION_STATE,
)
from core.db.models.order import Order
from core.db.models.order_history import OrderHistory
from core.db.models.user_subscription_snapshot import UserSubscriptionSnapshot
from core.dbmethods import get_order_creation_month
from core.dbmethods.user import get_user
from core.order.order_manager import (
    OrderManager,
    run_scheduled_orders,
    notify_timed_out_orders,
)
from core.order.actions.wine_expert import get_admin_order_url


def test_create_order(app, user, user_subscription, user_address):
    # Test
    OrderManager.create_order(user.id, user_subscription.id)

    # Check
    order = db.session.query(Order).filter_by(user_id=user.id).first()
    order_history = db.session.query(OrderHistory).filter_by(order_id=order.id).first()
    subscription_snapshot = db.session.query(
        UserSubscriptionSnapshot
    ).filter_by(order_id=order.id).first()

    assert order.state == STARTED_STATE
    assert order_history.state == STARTED_STATE

    for f in ('type', 'bottle_qty', 'budget'):
        assert getattr(subscription_snapshot, f) == \
               getattr(user_subscription, f)


@patch('core.order.order_manager.run_order')
def test_run_scheduled_orders(run_order_m, app, order, order_proposed):
    # Test
    run_scheduled_orders()

    # Check
    run_order_m.delay.assert_called_once_with(order.id)


@patch('core.order.actions.search.requests')
@patch('core.order.actions.wine_expert.send_mail')
@patch('core.order.actions.search.create_product_offers')
def test_run_action_after_started(
        create_product_offers_m,
        send_mail_m,
        requests_m,
        app,
        wine_expert,
        order,
        user,
        user_address,
        user_subscription2,
        source_1,
        source_2,
        theme_1,
        theme_2,
        theme_3,
        shipping_rate,
        salestax_rate,
        shipping_rate_2,
        salestax_rate_2
):
    user.primary_user_subscription.type = user_subscription2.type
    user.first_name = 'tuser new (updated) name'
    user_address.street1 = 'new (updated) street 1'
    user_address.street2 = 'new (updated) street 2'
    user_address.country = 'new (updated) country'
    user_address.city = 'new (updated) city'
    user_address.postcode = 1235
    user.phone = '+123212721237'
    user.selected_themes.extend([theme_1, theme_2, theme_3])
    db.session.commit()

    result = MagicMock()
    result.status_code = 200
    requests_m.get.return_value = result

    manager = OrderManager(order.id)

    # Test
    manager.run_action()

    requests_m.get.assert_called_with(
        '/api/search',
        params={
            'number_wines': 2,
            'wine_types': '["red"]',
            'themes': json.dumps([theme_2.id, theme_3.id]),
            'sources_budget': '{"%s": 82, "%s": 73}' % (source_1.id, source_2.id),
            'sent_wines': '[]'
        }
    )

    # Check
    assert order.action is None
    assert order.state == PROPOSED_TO_WINE_EXPERT_STATE

    states = [o.state for o in order.order_history]
    assert states == [STARTED_STATE, READY_TO_PROPOSE_STATE, PROPOSED_TO_WINE_EXPERT_STATE]

    # Make sure SearchAction updates order shipping info with latest data
    assert order.subscription.type == 'red'
    assert order.shipping_name == 'tuser new (updated) name'
    assert order.shipping_street1 == 'new (updated) street 1'
    assert order.shipping_street2 == 'new (updated) street 2'
    assert order.shipping_country == 'new (updated) country'
    assert order.shipping_city == 'new (updated) city'
    assert order.shipping_postcode == 1235
    assert order.shipping_phone == '+123212721237'

    order_url = get_admin_order_url(order.id)
    send_mail_m.assert_called_once_with(
        wine_expert.email,
        'New Order',
        'New order %s is available here: %s' % (order.id, order_url)
    )
    create_product_offers_m.assert_called_once_with(order.id, requests_m.get().json())


@patch('core.order.actions.support_admin.send_mail')
@patch('core.order.actions.search.requests')
def test_run_search_action_exception(
        requests_m,
        send_mail_m,
        app,
        wine_expert,
        order,
        user,
        user_address,
        user_subscription2,
        source_1,
        source_2,
        theme_1,
        theme_2,
        theme_3,
        shipping_rate,
        salestax_rate,
        shipping_rate_2,
        salestax_rate_2
):
    user.primary_user_subscription.type = user_subscription2.type
    user.selected_themes.extend([theme_1, theme_2, theme_3])
    db.session.commit()

    result = MagicMock()
    result.status_code = 400
    result.text = 'error'
    requests_m.get.return_value = result

    manager = OrderManager(order.id)

    # Test
    manager.run_action()

    requests_m.get.assert_called_with(
        '/api/search',
        params={
            'number_wines': 2,
            'wine_types': '["red"]',
            'themes': json.dumps([theme_2.id, theme_3.id]),
            'sources_budget': '{"%s": 82, "%s": 73}' % (source_1.id, source_2.id),
            'sent_wines': '[]'
        }
    )

    # Check
    assert order.action is None
    assert order.state == SEARCH_EXCEPTION_STATE

    states = [o.state for o in order.order_history]
    assert states == [STARTED_STATE, SEARCH_EXCEPTION_TO_NOTIFY_STATE, SEARCH_EXCEPTION_STATE]


@patch('core.order.actions.search.requests')
@patch('core.order.actions.wine_expert.send_mail')
@patch('core.order.actions.search.create_product_offers')
def test_run_action_after_started_with_sent_wines(
        create_product_offers_m,
        send_mail_m,
        requests_m,
        app,
        wine_expert,
        order,
        user,
        user_address,
        source_1,
        source_2,
        theme_1,
        theme_2,
        theme_3,
        shipping_rate,
        salestax_rate,
        shipping_rate_2,
        salestax_rate_2,
        old_completed_order,
        old_accepted_product_offer,
        old_accepted_offer_item_1,
        old_accepted_offer_item_2
):
    user.primary_user_subscription_id = order.subscription.id
    user.first_name = 'tuser new (updated) name'
    user_address.street1 = 'new (updated) street 1'
    user_address.street2 = 'new (updated) street 2'
    user_address.country = 'new (updated) country'
    user_address.city = 'new (updated) city'
    user_address.postcode = 1235
    user.phone = '+123212721237'
    user.selected_themes.extend([theme_1, theme_2, theme_3])
    db.session.commit()

    user.primary_user_subscription.type = 'red'
    db.session.commit()

    result = MagicMock()
    result.status_code = 200
    requests_m.get.return_value = result

    manager = OrderManager(order.id)

    # Test
    manager.run_action()

    requests_m.get.assert_called_with(
        '/api/search',
        params={
            'number_wines': 2,
            'wine_types': '["red"]',
            'themes': json.dumps([theme_2.id, theme_3.id]),
            'sources_budget': '{"%s": 82, "%s": 73}' % (source_1.id, source_2.id),
            'sent_wines': '[%s, %s]' % (
                old_accepted_offer_item_1.master_product_id, old_accepted_offer_item_2.master_product_id
            )
        }
    )

    # Check
    assert order.action is None
    assert order.state == PROPOSED_TO_WINE_EXPERT_STATE

    states = [o.state for o in order.order_history]
    assert states == [STARTED_STATE, READY_TO_PROPOSE_STATE, PROPOSED_TO_WINE_EXPERT_STATE]

    # Make sure SearchAction updates order shipping info with latest data
    assert order.subscription.type == 'red'
    assert order.shipping_name == 'tuser new (updated) name'
    assert order.shipping_street1 == 'new (updated) street 1'
    assert order.shipping_street2 == 'new (updated) street 2'
    assert order.shipping_state_region == 'New York'
    assert order.shipping_country == 'new (updated) country'
    assert order.shipping_city == 'new (updated) city'
    assert order.shipping_postcode == 1235
    assert order.shipping_phone == '+123212721237'

    order_url = get_admin_order_url(order.id)
    send_mail_m.assert_called_once_with(
        wine_expert.email,
        'New Order',
        'New order %s is available here: %s' % (order.id, order_url)
    )
    create_product_offers_m.assert_called_once_with(order.id, requests_m.get().json())


@patch('core.order.actions.user.boto3')
@patch('core.order.actions.user._send')
@patch('core.order.actions.base.boto3')
def test_run_action_after_approved(boto3_m, send_push_m, boto_m, app, order_proposed, user, user_address, device_token):
    client_m = MagicMock()
    boto3_m.client.return_value = client_m
    manager = OrderManager(order_proposed.id)

    # Test
    manager.run_action(APPROVE_ACTION)

    # Check
    assert order_proposed.action is None
    assert order_proposed.state == PROPOSED_TO_USER_STATE

    month = get_order_creation_month(order_proposed)
    msg = f'Your {month} wine selections are available! Please confirm quickly to ensure availability.'

    send_push_m.assert_called_once_with(
        boto_m.client(),
        device_token.token,
        '{"APNS": "{\\"aps\\": {\\"alert\\": \\"%s\\", \\"badge\\": 1, \\"domain\\": \\"magia.com\\"}}",'
        ' "default": "%s"}' % (msg, msg)
    )
    client_m.send_templated_email.assert_called_once()


@patch('core.order.actions.search.requests')
@patch('core.order.actions.wine_expert.send_mail')
@patch('core.order.actions.support_admin.send_mail')
@patch('core.order.actions.search.create_product_offers')
def test_run_action_exception(
        create_product_offers_m, support_mail_m, send_mail_m, requests_m, app, wine_expert, order, user_address,
        shipping_rate, salestax_rate
):
    send_mail_m.side_effect = Exception

    result = MagicMock()
    result.status_code = 200
    requests_m.get.return_value = result

    manager = OrderManager(order.id)

    # Test
    manager.run_action()

    # Check
    assert order.action is None
    assert order.state == NOTIFY_WINE_EXPERT_EXCEPTION_STATE

    states = [o.state for o in order.order_history]
    assert states == [
        STARTED_STATE,
        READY_TO_PROPOSE_STATE,
        NOTIFY_WINE_EXPERT_EXCEPTION_TO_NOTIFY_STATE,
        NOTIFY_WINE_EXPERT_EXCEPTION_STATE,
    ]

    order_url = get_admin_order_url(order.id)
    send_mail_m.assert_called_once_with(
        wine_expert.email,
        'New Order',
        'New order %s is available here: %s' % (order.id, order_url)
    )
    support_mail_m.assert_called_once()
    create_product_offers_m.assert_called_once_with(order.id, requests_m.get().json())


@patch('core.order.actions.user._send')
@patch('core.order.actions.user.boto3')
@patch('core.order.actions.base.boto3')
def test_place_order(
        boto3_mail_m, boto3_push_m, send_push_m, app, support_notified_order,
        accepted_product_offer, accepted_offer_item, device_token
):
    client_mail_m = MagicMock()
    boto3_mail_m.client.return_value = client_mail_m

    client_push_m = MagicMock()
    boto3_push_m.client.return_value = client_push_m

    # Test
    OrderManager(support_notified_order.id).run_action(PLACE_ORDER_ACTION)

    # Check
    client_mail_m.send_templated_email.assert_called_once()
    send_push_m.assert_called_once_with(
        client_push_m,
        device_token.token,
        '{"APNS": "{\\"aps\\": {\\"content-available\\": 1, \\"domain\\": \\"magia.com\\", \\"sound\\": \\"\\"}}"}'
    )

    assert support_notified_order.action is None
    assert support_notified_order.state == ORDER_PLACED_STATE


@patch('core.dbmethods.user.stripe')
@patch('core.order.actions.user.boto3')
@patch('core.order.actions.user._send')
@patch('core.order.actions.base.boto3')
def test_run_action_after_placed(
        boto3_m, send_push_m, boto_m, stripe_m, app, placed_order,
        placed_product_offer, user, user_address, device_token, placed_offer_item
):
    """After order is shipped charge must be captured and notification sent to the User"""
    client_m = MagicMock()
    boto3_m.client.return_value = client_m
    charge = MagicMock()
    stripe_m.Charge.retrieve.return_value = charge

    manager = OrderManager(placed_order.id)

    # Test
    manager.run_action(SET_SHIPPED_ACTION)

    # Check
    assert placed_order.action is None
    assert placed_order.state == USER_NOTIFIED_SHIPPED_STATE

    states = [o.state for o in placed_order.order_history]
    assert states == [
        STARTED_STATE, ORDER_PLACED_STATE, ORDER_SHIPPED_STATE, MONEY_CAPTURED_STATE, USER_NOTIFIED_SHIPPED_STATE
    ]

    send_push_m.assert_called_once()
    call_args = send_push_m.call_args[0]

    assert call_args[0] == boto_m.client()
    assert call_args[1] == device_token.token

    body_dct = json.loads(call_args[2])
    apns_dct = json.loads(body_dct['APNS'])
    assert apns_dct == {
        "aps": {
            "alert": "Your order is shipped!", "badge": 1,
            "domain": "magia.com", "subscriptionId": placed_order.id
        }
    }

    stripe_m.Charge.retrieve.assert_called_once_with(placed_product_offer.stripe_charge_id)
    charge.capture.assert_called_once()

    client_m.send_templated_email.assert_called_once()


@patch('core.order.order_manager.send_mail')
def test_notify_timed_out_orders(send_mail_m, app, order, timed_out_order):
    order_id = timed_out_order.id

    # Test
    notify_timed_out_orders()

    # Check
    order = Order.query.filter_by(id=order_id).first()
    assert order.timed_out is True

    send_mail_m.assert_called_once()
    assert str(order_id) in send_mail_m.call_args[0][2]

    # Check not notified second time
    notify_timed_out_orders()
    send_mail_m.assert_called_once()


@patch('core.order.actions.support_admin.datetime')
def test_next_month_order(
        datetime_m, app, user_notified_shipped_order_20150530, user, user_address
):
    """After order is completed new order should be created and scheduled for the next month"""
    datetime_m.utcnow.return_value = datetime(2015, 6, 15, 13, 13, 13, 13)
    datetime_m.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    manager = OrderManager(user_notified_shipped_order_20150530.id)

    # Test
    manager.run_action(SET_USER_RECEIVED_ACTION)

    # Check
    assert user_notified_shipped_order_20150530.action is None
    assert user_notified_shipped_order_20150530.state == COMPLETED_STATE

    states = [o.state for o in user_notified_shipped_order_20150530.order_history]
    assert states == [
        STARTED_STATE,
        USER_NOTIFIED_SHIPPED_STATE,
        USER_RECEIVED_STATE,
        COMPLETED_STATE,
    ]

    assert len(user.orders) == 2
    next_month_order = [o for o in user.orders if o.id != user_notified_shipped_order_20150530.id]
    assert len(next_month_order) == 1

    assert next_month_order[0].state == STARTED_STATE
    assert next_month_order[0].scheduled_for == datetime(2015, 6, 30, 13, 13, 13, 13)


@patch('core.order.actions.support_admin.datetime')
def test_next_month_order_long_time_ago(
        datetime_m, app, user_notified_shipped_order_20150530, user, user_address
):
    """
    After order is completed new order should be created and scheduled for right now
    (simulating the case when the user's subscription was inactive for a very long time and now was activated)
    """
    datetime_m.utcnow.return_value = datetime(2017, 5, 30, 13, 13, 13, 13)
    datetime_m.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    manager = OrderManager(user_notified_shipped_order_20150530.id)

    # Test
    manager.run_action(SET_USER_RECEIVED_ACTION)

    # Check
    assert user_notified_shipped_order_20150530.action is None
    assert user_notified_shipped_order_20150530.state == COMPLETED_STATE

    states = [o.state for o in user_notified_shipped_order_20150530.order_history]
    assert states == [
        STARTED_STATE,
        USER_NOTIFIED_SHIPPED_STATE,
        USER_RECEIVED_STATE,
        COMPLETED_STATE,
    ]

    assert len(user.orders) == 2
    next_month_order = [o for o in user.orders if o.id != user_notified_shipped_order_20150530.id]
    assert len(next_month_order) == 1

    assert next_month_order[0].state == STARTED_STATE
    assert next_month_order[0].scheduled_for == datetime(2017, 5, 30, 13, 13, 13, 13)


@patch('core.order.actions.support_admin.datetime')
@patch('core.dbmethods.datetime')
def test_dont_run_next_month_order_yet(
        datetime_m1, datetime_m2, app, user_notified_shipped_order_20150530, user, user_address
):
    datetime_m1.utcnow.return_value = datetime(2015, 6, 29, 13, 13, 13, 13)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect
    user_id = user.id

    manager = OrderManager(user_notified_shipped_order_20150530.id)
    manager.run_action(SET_USER_RECEIVED_ACTION)

    with patch('core.order.order_manager.run_order') as run_order_m:
        # Test
        run_scheduled_orders()

        # Check
        user = get_user(user_id)
        assert len(user.orders) == 2
        next_month_order = [o for o in user.orders if o.id != user_notified_shipped_order_20150530.id]
        assert len(next_month_order) == 1

        run_order_m.delay.assert_not_called()


@patch('core.order.actions.support_admin.datetime')
@patch('core.dbmethods.datetime')
def test_run_next_month_order_already(
        datetime_m1, datetime_m2, app, user_notified_shipped_order_20150530, user, user_address
):
    datetime_m1.utcnow.return_value = datetime(2017, 5, 30, 13, 13, 13, 13)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect
    user_id = user.id

    manager = OrderManager(user_notified_shipped_order_20150530.id)
    manager.run_action(SET_USER_RECEIVED_ACTION)

    with patch('core.order.order_manager.run_order') as run_order_m:
        # Test
        run_scheduled_orders()

        # Check
        user = get_user(user_id)
        assert len(user.orders) == 2
        next_month_order = [o for o in user.orders if o.id != user_notified_shipped_order_20150530.id]
        assert len(next_month_order) == 1

        run_order_m.delay.assert_called_once_with(next_month_order[0].id)


@patch('core.order.actions.support_admin.datetime')
@patch('core.dbmethods.datetime')
def test_dont_run_next_month_order_subscription_suspended(
        datetime_m1, datetime_m2, app, user_notified_shipped_order_20150530, user, user_address
):
    datetime_m1.utcnow.return_value = datetime(2017, 5, 30, 13, 13, 13, 13)
    datetime_m1.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
    datetime_m2.utcnow.return_value = datetime_m1.utcnow.return_value
    datetime_m2.side_effect = datetime_m1.side_effect
    user_id = user.id

    user.primary_user_subscription.state = SUBSCRIPTION_SUSPENDED_STATE
    db.session.commit()

    manager = OrderManager(user_notified_shipped_order_20150530.id)
    manager.run_action(SET_USER_RECEIVED_ACTION)

    with patch('core.order.order_manager.run_order') as run_order_m:
        # Test
        run_scheduled_orders()

        # Check
        user = get_user(user_id)
        assert len(user.orders) == 2
        next_month_order = [o for o in user.orders if o.id != user_notified_shipped_order_20150530.id]
        assert len(next_month_order) == 1

        run_order_m.delay.assert_not_called()
