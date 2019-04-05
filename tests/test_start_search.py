# pylint: disable=no-member,unused-argument,invalid-name
from unittest.mock import patch

from core import config

from core.db.models import db
from core.db.models.order import Order
from core.db.models.order_history import OrderHistory
from core.db.models.user_subscription_snapshot import UserSubscriptionSnapshot
from core.db.models.common import STARTED_STATE
from core.dbmethods.user import get_user


@patch('core.graphql.schemas.user.send_template_email')
def test_start_search(send_mail_m, graphql_client, user, user_subscription, user_address):
    user_id = user.id

    mutation = """mutation {
        startSearch(input: {}) {clientMutationId}}"""

    # Test
    graphql_client.post(mutation)

    # Check
    order = db.session.query(Order).filter_by(user_id=user.id).first()
    order_history = db.session.query(OrderHistory).filter_by(order_id=order.id).first()
    subscription_snapshot = db.session.query(
        UserSubscriptionSnapshot
    ).filter_by(order_id=order.id).first()

    assert order.state == STARTED_STATE
    assert order_history.state == STARTED_STATE

    user = get_user(user_id)
    for f in ('type', 'bottle_qty', 'budget'):
        assert getattr(subscription_snapshot, f) == \
               getattr(user.primary_user_subscription, f)

    send_mail_m.assert_called_once_with(
        user.email, 'welcome',
        {
            'name': user.first_name,
            'deeplink': config.SERVER_DEEPLINK_URL + '/subscriptions/',
        }
    )
