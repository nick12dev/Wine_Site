# pylint: disable=no-member
import json
import logging
from datetime import datetime

import requests

from core import config
from core.dbmethods import (
    get_order,
    get_sources_budget,
    state_to_postcode,
)
from core.dbmethods.product import (
    create_product_offers,
    delete_product_offers,
)
from core.dbmethods.user import (
    get_all_accepted_wines,
    get_sources_shipping_to,
    get_user_themes,
)
from core.db.models import (
    db,
    NOTIFY_WINE_EXPERT_ACTION,
    READY_TO_PROPOSE_STATE,
    SEARCH_ACTION,
    STARTED_STATE,
)
from core.order.actions.base import Action
from core.order.exceptions import OrderException


def do_search(number_wines, wine_types, themes, sources_budget, sent_wines):
    params = {
        'number_wines': number_wines,
        'wine_types': json.dumps(wine_types),
        'themes': json.dumps(themes),
        'sources_budget': json.dumps(sources_budget),
        'sent_wines': json.dumps(sent_wines),
    }
    url = config.SEARCH_API_URL + '/api/search'
    logging.info('calling search api: "%s" with params: %s', url, params)
    response = requests.get(url, params=params)
    logging.info('got response: %s', response.text)
    if response.status_code > 500:
        response.raise_for_status()
    elif response.status_code != 200:
        raise OrderException(response.text)
    return response.json()


def get_wine_types(subscription_type):
    if subscription_type == 'mixed':
        return ['red', 'white']
    else:
        return [subscription_type]


class SearchAction(Action):

    def run(self, order_id):
        logging.info('running SearchAction')
        order = get_order(order_id)
        themes = get_user_themes(order.user_id)
        subscription = order.subscription
        bottle_qty = subscription.bottle_qty
        wine_types = get_wine_types(subscription.type)
        budget = subscription.budget

        address = order.user.primary_user_address
        order.shipping_name = order.user.first_name
        order.shipping_street1 = address.street1
        order.shipping_street2 = address.street2
        order.shipping_state_region = address.state_region
        order.shipping_country = address.country
        order.shipping_city = address.city
        order.shipping_postcode = address.postcode
        order.shipping_phone = order.user.phone
        order.subscription_snapshot.type = subscription.type
        order.subscription_snapshot.bottle_qty = bottle_qty
        order.subscription_snapshot.budget = budget
        db.session.flush()

        user_id = order.user.id
        user_state_region = order.user.primary_user_address.state_region

        state_postal_code = state_to_postcode(user_state_region)
        sources = get_sources_shipping_to(state_postal_code)
        if not sources:
            raise OrderException(
                'No source found that ships to User: %s in state_region: %s' %
                (user_id, user_state_region)
            )

        sources_budget = get_sources_budget(sources, budget, bottle_qty, order.shipping_postcode)
        if not sources_budget:
            raise OrderException('No available shipping or tax info')

        sent_wines = get_all_accepted_wines(user_id)

        # call search API
        products = do_search(bottle_qty, wine_types, themes, sources_budget, sent_wines)
        logging.info('got products: %s', products)

        # update DB
        delete_product_offers(order_id)
        db.session.flush()
        create_product_offers(order_id, products)

        if order.scheduled_for is None:
            subscription.last_order_searched_at = datetime.utcnow()
        else:
            subscription.last_order_searched_at = order.scheduled_for

        return NOTIFY_WINE_EXPERT_ACTION, READY_TO_PROPOSE_STATE


class RetrySearchAction(Action):

    def run(self, order_id):
        logging.info('running RetrySearchAction order_id: %s', order_id)

        get_order(order_id).scheduled_for = datetime.utcnow()

        return SEARCH_ACTION, STARTED_STATE
