# pylint: disable=no-member

import requests
from decimal import Decimal

from sqlalchemy import text

from core import (
    config,
    to_int,
    to_decimal,
)
from core.db.models import db
from core.db.models.master_product import MasterProduct
from core.db.models.product_offer import ProductOffer
from core.db.models.offer_item import OfferItem
from core.db.models.source import Source
from core.db.models.order import Order
from core.dbmethods import (
    get_order,
    get_shipping_cost,
    get_tax_rate,
)
from core.order.exceptions import OrderException


def get_master_product(master_product_id):
    return db.session.query(MasterProduct).filter_by(id=master_product_id).first()


def get_priority(products):
    """Returns dict of {offer index (position in products list): priority}"""
    product_scores = []
    for n, _products in enumerate(products):
        scores = sum([int(p['rating']) for p in _products])
        product_scores.append((n, scores))

    sorted_products = sorted(product_scores, key=lambda x: x[1])

    offer_priority = {}
    for n, el in enumerate(sorted_products):
        offer_priority[el[0]] = n

    return offer_priority


def get_product_by_sku(sku):
    q = text("""
        select master_product_id, source_id
        from pipeline_attribute_values
        where attribute_id = 19 and value_text = :sku;
    """)

    res = db.session.execute(q, {'sku': sku}).first()
    if res is None:
        return

    m_product_id, source_id = res
    url = (config.SEARCH_API_URL +
           f'/api/search/{source_id}/product_data/{m_product_id}')
    response = requests.get(url)
    if response.status_code != 200:
        raise OrderException(response.text)
    res = response.json()['data']
    res = res and res[0] or {}
    return res


def create_offer_item_from_dict(product_dict, product_offer_id):
    offer_item = OfferItem(
        product_offer_id=product_offer_id,
        master_product_id=product_dict['master_product_id'],
        name=product_dict.get('wine_name') or '',
        score_num=to_int(product_dict.get('rating')),
        image=product_dict['img_url'],
        price=to_decimal(product_dict.get('price')),
        description=product_dict.get('short_desc', ''),
        location=product_dict.get('region', ''),
        brand=product_dict.get('brand', ''),
        sku=product_dict.get('sku', ''),
        qoh=product_dict.get('qoh'),
        msrp=to_decimal(product_dict.get('msrp')),
        product_url=product_dict.get('product_url'),
        highlights=product_dict.get('highlights'),
        varietals=product_dict.get('varietals'),
        best_theme_id=to_int(product_dict.get('best_theme'))
    )
    db.session.add(offer_item)
    db.session.flush()

    offer_item.prof_reviews = [{
        'name': r.reviewer_name,
        'score': to_int(r.review_score)
    } for r in offer_item.product_reviews if r.review_score]
    # TODO otereshchenko: optimize db fetching of offer_item.product_reviews for batch

    return offer_item


def delete_product_offers(order_id):
    OfferItem.query.filter(OfferItem.product_offer_id.in_(
        db.session.query(ProductOffer.id).filter(ProductOffer.order_id == order_id).subquery()
    )).delete(synchronize_session='fetch')
    ProductOffer.query.filter(
        ProductOffer.order_id == order_id
    ).delete(synchronize_session='fetch')


def create_product_offers(order_id, products_list):
    order = get_order(order_id)
    products = products_list[0]

    master_product_id = products[0]['master_product_id']
    master_product = get_master_product(master_product_id)

    source = db.session.query(Source).filter_by(id=master_product.source_id).first()

    product_offer = ProductOffer(
        order_id=order_id,
        source_id=master_product.source_id,
        wine_type=order.subscription.type,
        priority=1,
        name=source.name,
        accepted=True
    )
    db.session.add(product_offer)
    db.session.flush()

    for product in products:
        create_offer_item_from_dict(product, product_offer.id)

    db.session.flush()
    populate_offer_costs(product_offer)


def get_product_cost(offer_items):
    product_cost = Decimal()
    for offer_item in offer_items:
        product_cost += Decimal(offer_item.price)
    return product_cost


def recalc_total_cost(offer_items, salestax_cost, shipping_cost):
    product_cost = get_product_cost(offer_items)
    total_cost = product_cost + salestax_cost + shipping_cost

    return total_cost, product_cost


def populate_offer_costs(product_offer):
    def get_total_price(offer_items, salestax_rate, shipping_cost):
        _salestax_rate = Decimal(salestax_rate)
        _shipping_cost = Decimal(shipping_cost)
        _product_cost = get_product_cost(offer_items)

        salestax_cost = _product_cost * salestax_rate
        _total_cost = _product_cost + salestax_cost + shipping_cost

        return _total_cost, _product_cost, salestax_cost

    bottle_qty = len(product_offer.offer_items)
    postcode = product_offer.order.shipping_postcode
    shipping_cost = get_shipping_cost(product_offer.source_id, bottle_qty, postcode)
    salestax_rate = get_tax_rate(product_offer.source_id, postcode)

    total_cost, product_cost, salestax_cost = get_total_price(
        product_offer.offer_items, salestax_rate, shipping_cost
    )

    product_offer.bottle_qty = bottle_qty
    product_offer.total_cost = total_cost
    product_offer.salestax_rate = salestax_rate
    product_offer.shipping_cost = shipping_cost
    product_offer.salestax_cost = salestax_cost
    product_offer.product_cost = product_cost
    db.session.flush()


def get_accepted_product_offer(order_id):
    offer = db.session.query(ProductOffer).join(
        Order
    ).filter(
        Order.id == order_id,
        ProductOffer.accepted == True
    ).first()

    return offer
