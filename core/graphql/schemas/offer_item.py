import logging

import graphene
from graphene import relay

from core.db.models import db
from core.db.models.master_product import MasterProduct
from core.db.models.offer_item import OfferItem as OfferItemModel
from core.db.models.product_offer import ProductOffer as ProductOfferModel
from core.dbmethods.product import (
    get_product_by_sku,
    create_offer_item_from_dict,
    populate_offer_costs,
)
from core.graphql.schemas import (
    RegisteredUserObjectType,
    build_product_reviews_cached,
    ProductReview,
    from_global_id_assert_type,
)


class OfferItem(RegisteredUserObjectType):
    class Meta:
        model = OfferItemModel
        interfaces = (relay.Node,)
        only_fields = (
            'brand',
            'name',
            'score_num',
            'image',
            'description',
            'location',
            'highlights',
            'varietals',
            'qty',
            'sku',
            'qoh',
            'product_url',
            'best_theme',
        )

    price = graphene.Field(graphene.String)
    msrp = graphene.Field(graphene.String)
    highlights = graphene.List(graphene.String)
    varietals = graphene.List(graphene.String)

    product_reviews = graphene.List(ProductReview)
    top_product_review = graphene.Field(ProductReview)

    @staticmethod
    def get_model_owner(model):
        return model.product_offer.order.user

    @staticmethod
    def resolve_price(model, info):
        if model.price is not None:
            return str(model.price)

    @staticmethod
    def resolve_msrp(model, info):
        if model.msrp is not None:
            return str(model.msrp)

    @staticmethod
    def resolve_product_reviews(model, info):
        return build_product_reviews_cached(model)

    @staticmethod
    def resolve_top_product_review(model, info):
        reviews = build_product_reviews_cached(model)
        if reviews:
            return reviews[0]


class OfferItemReplacementInput(graphene.InputObjectType):
    offer_item_id = graphene.ID(required=True)
    new_sku = graphene.String()
    new_best_theme_id = graphene.String()


def replace_offer_items(order_inp, order):
    replacements_inp = order_inp.get('offer_item_replacements')
    if replacements_inp is None:
        return

    replacement_inp_dict = {}
    for replacement_inp in replacements_inp:
        offer_item_id = from_global_id_assert_type(replacement_inp.offer_item_id, 'OfferItem')

        replacement_inp_dict[offer_item_id] = replacement_inp

    offer_items = OfferItemModel.query.join(OfferItemModel.product_offer).filter(
        ProductOfferModel.order_id == order.id,
        OfferItemModel.id.in_(replacement_inp_dict.keys())
    )

    updated_product_offer_dict = {}
    for offer_item in offer_items:
        replacement_inp = replacement_inp_dict[offer_item.id]

        new_sku = replacement_inp.get('new_sku')
        if new_sku and new_sku != offer_item.sku:
            product_dict = get_product_by_sku(new_sku)

            if product_dict:
                product_offer = offer_item.product_offer
                new_master_product = MasterProduct.query.get(product_dict['master_product_id'])

                if new_master_product.source_id == product_offer.source_id:
                    best_theme_id = offer_item.best_theme_id
                    db.session.delete(offer_item)

                    offer_item = create_offer_item_from_dict(product_dict, product_offer.id)
                    offer_item.best_theme_id = best_theme_id

                    updated_product_offer_dict[product_offer.id] = product_offer
                else:
                    logging.error(
                        'Cannot replace offer item with id=%s with product by sku=%s - '
                        'the source id should be the same (expected=%s, found=%s)',
                        offer_item.id,
                        new_sku,
                        product_offer.source_id,
                        new_master_product.source_id,
                    )
            else:
                logging.error(
                    'Cannot replace offer item with id=%s - product with sku=%s was not found',
                    offer_item.id,
                    new_sku,
                )

        new_best_theme_id = replacement_inp.get('new_best_theme_id')
        if new_best_theme_id:
            offer_item.best_theme_id = from_global_id_assert_type(
                new_best_theme_id, 'Theme'
            )

    db.session.flush()

    for product_offer in updated_product_offer_dict.values():
        populate_offer_costs(product_offer)
