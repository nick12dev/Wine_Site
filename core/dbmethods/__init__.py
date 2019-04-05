#
# pylint: disable=no-member,comparison-with-callable,undefined-variable,singleton-comparison
import logging
from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy.orm import aliased
from sqlalchemy import or_

from core import config
from core.db.models import (
    db,
    SEARCH_ACTION,
    STARTED_STATE,
    SUBSCRIPTION_ACTIVE_STATE,
    ORDER_SHIPPED_STATE,
    COMPLETED_STATE,
    EXCEPTION_STATE_SET,
)
from core.db.models.order import Order
from core.db.models.order_history import OrderHistory
from core.db.models.pipeline_sequence import PipelineSequence
from core.db.models.user import User
from core.db.models.user_address import UserAddress
from core.db.models.device_token import DeviceToken
from core.db.models.shipping_rate import ShippingRate
from core.db.models.source_location import SourceLocation
from core.db.models.salestax_rate import SalestaxRate
from core.db.models.user_subscription import UserSubscription
from core.db.models.user_subscription_snapshot import UserSubscriptionSnapshot

USA_STATES_POSTCODE = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'SouthCarolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
    'American Samoa': 'AS',
    'District of Columbia': 'DC',
    'Federated States of Micronesia': 'FM',
    'Guam': 'GU',
    'Marshall Islands': 'MH',
    'Northern Mariana Islands': 'MP',
    'Palau': 'PW',
    'Puerto Rico': 'PR',
    'Virgin Islands': 'VI',
}

MONTH = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
]


def get_order_creation_month(order):
    return MONTH[order.order_history[0].created_at.month - 1]


def state_to_postcode(state_name):
    return USA_STATES_POSTCODE.get(state_name)


def get_orders_to_run():
    orders = db.session.query(
        Order
    ).join(
        Order.subscription
    ).filter(
        Order.scheduled_for <= datetime.utcnow(),
        Order.action != None,
        or_(
            UserSubscription.state == SUBSCRIPTION_ACTIVE_STATE,
            Order.state != STARTED_STATE
        ),
    ).all()
    db.session.close()
    return orders


def get_timed_out_orders():
    orders = db.session.query(
        Order
    ).join(
        Order.subscription
    ).filter(
        UserSubscription.state == SUBSCRIPTION_ACTIVE_STATE,
        Order.state_changed_at < datetime.utcnow() - timedelta(days=config.ORDER_TIMEOUT_DAYS),
        Order.timed_out == False,
        Order.state.notin_(
            {STARTED_STATE, ORDER_SHIPPED_STATE, COMPLETED_STATE} | EXCEPTION_STATE_SET
        )
    ).all()
    return orders


def get_order(order_id):
    return db.session.query(Order).filter_by(id=order_id).first()


def get_current_order(user_id):
    order = db.session.query(Order).filter_by(
        user_id=user_id,
    ).order_by(
        Order.created_at.desc()
    ).first()
    return order


def get_order_tracking_url(order):
    try:
        return order.shipping_method.carrier.tracking_url_template.format(
            order.shipping_tracking_num
        )
    except Exception as e:
        logging.warning("Can not get tracking url for order: %s: %s", order.id, e)


def get_default_wine_expert():
    expert = db.session.query(
        User
    ).filter(User.wine_expert_id == None).first()
    return expert


def create_order(user_id, subscription_id, scheduled_for=None):
    address, user = db.session.query(
        UserAddress, User
    ).join(
        User, User.primary_user_address_id == UserAddress.id
    ).filter(
        User.id == user_id
    ).first()

    subscription = db.session.query(
        UserSubscription
    ).filter_by(id=subscription_id).first()

    order = Order(
        subscription_id=subscription_id,
        user_id=user_id,
        state=STARTED_STATE,
        action=SEARCH_ACTION,
        shipping_name=user.first_name,
        shipping_street1=address.street1,
        shipping_street2=address.street2,
        shipping_state_region=address.state_region,
        shipping_country=address.country,
        shipping_city=address.city,
        shipping_postcode=address.postcode,
        shipping_phone=user.phone
    )
    if scheduled_for is not None:
        order.scheduled_for = scheduled_for
    db.session.add(order)
    db.session.commit()

    order.order_number = f'{order.id:07}'

    order_history = OrderHistory(
        order_id=order.id,
        state=order.state
    )
    subscription_snapshot = UserSubscriptionSnapshot(
        order_id=order.id,
        type=subscription.type,
        bottle_qty=subscription.bottle_qty,
        budget=subscription.budget
    )
    db.session.add(order_history)
    db.session.add(subscription_snapshot)
    db.session.commit()
    return order


def move_order(order, action, state, exception_msg=None):
    order.action = action
    order.state = state
    order.scheduled_for = None
    order.exception_message = exception_msg

    parent_order_history = db.session.query(OrderHistory).filter_by(
        order_id=order.id
    ).order_by(OrderHistory.created_at.desc()).first()

    order_history = OrderHistory(
        order_id=order.id,
        state=order.state,
        parent_id=parent_order_history.id,
        exception_message=exception_msg
    )

    db.session.add(order_history)
    db.session.flush()
    order.state_changed_at = order_history.created_at
    db.session.commit()

    return order


def get_wine_expert_for_order(order_id):
    expert = aliased(User)

    return db.session.query(
        expert
    ).join(
        User, User.wine_expert_id == expert.id
    ).join(
        Order, Order.user_id == User.id
    ).filter(User.id == Order.user_id).first()


def save_device_token(user_id, token):
    exists = db.session.query(
        DeviceToken
    ).filter_by(token=token).all()

    if exists:
        return

    device_token = DeviceToken(
        user_id=user_id,
        token=token
    )
    db.session.add(device_token)
    db.session.commit()


def get_shipping_cost(source_id, bottle_qty, postcode):
    try:
        shipping_cost = db.session.query(ShippingRate.shipping_cost).join(SourceLocation).filter(
            SourceLocation.source_id == source_id,
            ShippingRate.bottle_qty == bottle_qty,
            ShippingRate.from_postcode <= postcode,
            ShippingRate.to_postcode >= postcode
        ).first()
    except Exception as e:
        logging.exception(
            'Error when getting shipping cost for source: %s, postcode: %s, bottle_qty: %s, %s' %
            (source_id, postcode, bottle_qty, e)
        )
        raise

    if shipping_cost is None:
        raise Exception(
            'Shipping cost not found for source: %s, postcode: %s, bottle_qty: %s' %
            (source_id, postcode, bottle_qty)
        )

    return shipping_cost[0]


def get_tax_rate(source_id, postcode):
    try:
        tax_rate = db.session.query(SalestaxRate.taxrate).join(SourceLocation).filter(
            SourceLocation.source_id == source_id,
            SalestaxRate.from_postcode <= postcode,
            SalestaxRate.to_postcode >= postcode
        ).first()
    except Exception as e:
        logging.exception(
            'Error when getting tax rate for source: %s, postcode: %s, %s' %
            (source_id, postcode, e)
        )
        raise

    if tax_rate is None:
        raise Exception(
            'Tax rate not found for source: %s, postcode: %s' %
            (source_id, postcode)
        )

    return tax_rate[0]


def get_sources_budget(sources, budget, bottle_qty, postcode):
    res = {}
    for source_id in sources:
        try:
            shipping_cost = get_shipping_cost(source_id, bottle_qty, postcode)
            tax_rate = get_tax_rate(source_id, postcode)

            res[source_id] = int((budget - shipping_cost) / (1 + tax_rate))
        except Exception:
            logging.exception(
                'Error when getting shipping or tax rates for source: %s' % source_id
            )

    return res


def fetch_schedules_by_ids(schedule_ids):
    return PipelineSequence.query.filter(
        PipelineSequence.id.in_(schedule_ids)
    )
