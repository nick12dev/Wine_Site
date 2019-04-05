#
# pylint: disable=no-member,invalid-name
import json
import logging
import re
from distutils.util import strtobool
from random import randint

import stripe
from isounidecode import unidecode
from stripe.error import StripeError
from sqlalchemy.exc import IntegrityError

from core import (
    config,
    normalize_text,
)
from core.db.models import db
from core.db.models.theme import Theme
from core.db.models.theme_group import ThemeGroup
from core.db.models.user import User
from core.db.models.offer_item import OfferItem
from core.db.models.product_offer import ProductOffer
from core.db.models.order import Order
from core.db.models.source import Source
from core.db.models.source_location import SourceLocation
from core.dbmethods.product import get_accepted_product_offer
from core.dbmethods import (
    get_order,
    USA_STATES_POSTCODE,
    get_default_wine_expert,
    MONTH,
    get_order_tracking_url,
)


def get_cognito_attr_dict(cognito_user, attributes_key='Attributes'):
    attrs = cognito_user.get(attributes_key, {})
    if not isinstance(attrs, dict):
        attrs = {a['Name']: a['Value'] for a in attrs}
    return attrs


def populate_most_of_cognito_fields(
        user, cognito_sub, cognito_user, attributes_key='Attributes', clear_missing_data=True
):
    cognito_user_properties = {'Enabled', 'UserStatus', attributes_key}
    if not all(prop in cognito_user for prop in cognito_user_properties):
        logging.warning(
            'Not all cognito user properties are present for user with subject=%s, '
            'Expected: %s, Found: %s',
            cognito_sub,
            cognito_user_properties,
            cognito_user.keys(),
        )

    user.exists_in_cognito = True
    user.cognito_enabled = cognito_user.get(
        'Enabled', None if clear_missing_data else user.cognito_enabled
    )
    user.cognito_status = cognito_user.get(
        'UserStatus', 'UNKNOWN' if clear_missing_data else user.cognito_status
    )

    cognito_attrs = get_cognito_attr_dict(cognito_user, attributes_key=attributes_key)

    cognito_user_attributes = {'email_verified', 'phone_number_verified', 'email', 'phone_number'}
    if not all(a in cognito_attrs for a in cognito_user_attributes):
        logging.warning(
            'Not all cognito user attributes are present for user with subject=%s, '
            'Expected: %s, Found: %s',
            cognito_sub,
            cognito_user_attributes,
            cognito_attrs.keys(),
        )

    try:
        cognito_email_verified_attr = cognito_attrs['email_verified']
    except KeyError:
        if clear_missing_data:
            user.cognito_email_verified = None
    else:
        user.cognito_email_verified = None if cognito_email_verified_attr.lower() == 'null' else strtobool(
            cognito_email_verified_attr
        )

    try:
        cognito_phone_verified_attr = cognito_attrs['phone_number_verified']
    except KeyError:
        if clear_missing_data:
            user.cognito_phone_verified = None
    else:
        user.cognito_phone_verified = None if cognito_phone_verified_attr.lower() == 'null' else strtobool(
            cognito_phone_verified_attr
        )

    user.email = cognito_attrs.get('email', None if clear_missing_data else user.email)
    user.phone = cognito_attrs.get('phone_number', None if clear_missing_data else user.phone)


def populate_cognito_display_status(user):
    user.cognito_display_status = ' / '.join([
        'Enabled' if user.cognito_enabled else 'Disabled',
        user.cognito_status or 'UNKNOWN',
    ])


def create_user(cognito_sub, assign_wine_expert=True):
    user = User(
        cognito_sub=cognito_sub,
        exists_in_cognito=None,
        cognito_enabled=False,
        cognito_status='UNKNOWN',
        cognito_display_status='UNKNOWN',
        cognito_phone_verified=False,
        cognito_email_verified=False,
    )
    if assign_wine_expert:
        # Assign Wine Expert
        wine_expert = get_default_wine_expert()
        user.wine_expert_id = wine_expert.id
    db.session.add(user)
    db.session.flush()

    user.user_number = f'{user.id:07}'
    db.session.commit()
    return user


def get_user(user_id):
    return db.session.query(User).filter_by(id=user_id).first()


def get_user_by_sub(cognito_sub):
    return User.query.filter(User.cognito_sub == cognito_sub).order_by(User.id.asc()).first()


def get_user_by_username(username):
    return User.query.filter(User.username == username).one()


def get_or_create_user(cognito_sub):
    user = get_user_by_sub(cognito_sub)
    if not user:
        try:
            db.session.commit()
            user = create_user(cognito_sub)
        except IntegrityError:
            db.session.rollback()
            user = get_user_by_sub(cognito_sub)
            if not user:
                raise
    return user


def generate_username(first_name, last_name):
    username = '.'.join(' '.join(filter(None, (first_name, last_name))).replace('.', ' ').split())
    try:
        username = unidecode(username, 'ascii').decode('ascii')
    except:
        logging.warning('Failed to unidecode username: %s', username, exc_info=True)
    return ''.join([c if re.match(r'[a-zA-Z0-9.\-_]', c) else '_' for c in username]).lower()


def populate_automatic_username(user):
    db.session.commit()
    if user.username_set_manually and user.username:
        return

    old_username = user.username or ''
    new_username = generate_username(user.first_name, user.last_name)

    if old_username.startswith(new_username):
        old_username_suffix = old_username[len(new_username):]

        if not old_username_suffix:
            return

        try:
            int(old_username_suffix)
            return
        except ValueError:
            pass

    for i in range(10):
        final_username = new_username
        try:
            if i > 0:
                final_username += str(randint(1000, 9999))
                logging.warning('Alternative automatic username generated: %s', final_username)

            user.username = final_username
            db.session.commit()
            break
        except IntegrityError:
            logging.warning('Collision of automatic username: %s', final_username)
            db.session.rollback()


def get_stripe_customer(customer_id):
    stripe.api_key = config.STRIPE_SECRET_KEY
    customer = stripe.Customer.retrieve(customer_id)

    return customer


def save_stripe_customer_id(user_id, token):
    stripe.api_key = config.STRIPE_SECRET_KEY

    user = get_user(user_id)

    try:
        if user.stripe_customer_id is not None:
            customer = get_stripe_customer(user.stripe_customer_id)
            stripe.Customer.modify(customer.id, source=token)
        else:
            customer = stripe.Customer.create(
                source=token,
                email=user.email
            )
            # Save customer id
            user.stripe_customer_id = customer.id
            db.session.add(user)
            db.session.commit()
    except StripeError as e:
        logging.exception('Error when creating Stripe Customer: %s', e)
        raise Exception(e._message)
    except Exception as e:
        logging.exception('Error when creating Stripe Customer: %s', e)
        raise Exception('Unknown error when saving Stripe Customer')


def get_credit_card(user_id):
    logging.info('getting card info for user: %s', user_id)

    user = get_user(user_id)
    try:
        customer = get_stripe_customer(user.stripe_customer_id)
        card = customer.sources.data[0]
    except Exception as e:
        logging.exception('Error when getting card: %s', e)
        return
    else:
        return {
            'brand': card.brand,
            'country': card.country,
            'exp_month': card.exp_month,
            'exp_year': card.exp_year,
            'last4': card.last4,
            'name': card.name,
        }


def authorize_payment(order_id):
    logging.info('authorizing payment for order: %s', order_id)
    order = get_order(order_id)
    customer = get_stripe_customer(order.user.stripe_customer_id)

    offer = get_accepted_product_offer(order_id)

    charge = stripe.Charge.create(
        amount=int(offer.total_cost * 100),
        currency='usd',
        customer=customer.id,
        capture=False
    )

    offer.stripe_charge_id = charge.id
    db.session.commit()


def capture_payment(order_id):
    offer = get_accepted_product_offer(order_id)

    try:
        stripe.api_key = config.STRIPE_SECRET_KEY
        charge = stripe.Charge.retrieve(offer.stripe_charge_id)
        response = charge.capture()
        logging.info('charge.capture response: %s', response)
    except Exception as e:
        logging.exception('Error when getting card: %s', e)
        raise


def payment_should_be_skipped(order_id):
    if config.SKIP_PAYMENT:
        return True

    if config.ENABLE_MAGIC_CREDIT_CARD:
        try:
            def normalize_name(name):
                return ' '.join(name.split()).lower()

            magic_credit_card = json.loads(config.MAGIC_CREDIT_CARD_JSON)
            magic_brand = magic_credit_card['brand']
            magic_country = magic_credit_card['country']
            magic_exp_month = magic_credit_card['exp_month']
            magic_exp_year = magic_credit_card['exp_year']
            magic_last4 = magic_credit_card['last4']
            magic_name = normalize_name(magic_credit_card['name'])

            user_credit_card = get_credit_card(get_order(order_id).user_id)
            return magic_brand == user_credit_card['brand'] and \
                   magic_country == user_credit_card['country'] and \
                   magic_exp_month == user_credit_card['exp_month'] and \
                   magic_exp_year == user_credit_card['exp_year'] and \
                   magic_last4 == user_credit_card['last4'] and \
                   magic_name == normalize_name(user_credit_card['name'])
        except:
            logging.exception('Failed to compare user\'s credit card to MAGIC_CREDIT_CARD_JSON')
            return False
    return False


def get_all_accepted_wines(user_id):
    res = db.session.query(OfferItem.master_product_id).join(
        ProductOffer, Order
    ).filter(
        ProductOffer.accepted.is_(True),
        Order.user_id == user_id
    ).all()
    return [el[0] for el in res]


def get_sources_shipping_to(state_postal_code):
    sources = db.session.query(Source.id).join(SourceLocation).filter(
        SourceLocation.ship_to_regions.contains([state_postal_code])
    ).all()
    return [s[0] for s in sources]


def get_user_order_data(order_id):
    order = get_order(order_id)
    tracking_url = get_order_tracking_url(order)

    user = order.user
    shipping_address = {
        'name': user.first_name or '',
        'city': order.shipping_city,
        'street': order.shipping_street1,
        'state': USA_STATES_POSTCODE[order.shipping_state_region],
        'zipcode': order.shipping_postcode,
        'email': user.email,
        'phone': user.phone,
    }

    product_offer = order.accepted_offers[0]
    products = []
    for product in product_offer.offer_items:
        products.append({
            'name': product.name,
            'price': str(product.price),
            'sku': product.sku or '',
        })

    carrier = ''
    if order.shipping_method:
        carrier = order.shipping_method.carrier.carrier

    return {
        'order': {
            'url': 'url',
            'number': order.order_number,
            'month': MONTH[order.month - 1],
            'tracking_number': order.shipping_tracking_num,
            'tracking_url': tracking_url or '',
            'shipping_date': str(order.shipping_date),
            'carrier': carrier,
            'deeplink': '%s/subscriptions/?id=%s' % (config.SERVER_DEEPLINK_URL, order_id),
        },
        'billing_address': shipping_address,
        'shipping_address': shipping_address,
        'products': products,
        'total_cost': str(product_offer.total_cost),
        'product_cost': str(product_offer.product_cost),
        'salestax_cost': str(product_offer.salestax_cost),
        'shipping_cost': str(product_offer.shipping_cost),
        'source_name': product_offer.source.name,
    }


def get_user_themes(user_id):
    themes = db.session.query(Theme.id).join(
        Theme.users_who_selected
    ).join(
        Theme.theme_group
    ).filter(
        ThemeGroup.is_active != False,
        User.id == user_id,
    ).all()
    return [t[0] for t in themes]
