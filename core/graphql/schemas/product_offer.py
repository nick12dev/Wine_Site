# pylint: disable=unused-argument,redefined-builtin
import logging
from decimal import Decimal

import graphene
from graphene import relay
from sqlalchemy.orm import (
    selectinload,
    joinedload,
)

from core.cognito import registered_user_permission
from core.db.models.product_offer import ProductOffer as ProductOfferModel
from core.dbmethods.product import recalc_total_cost
from core.graphql.schemas import (
    RegisteredUserObjectType,
    OptimizeResolveTuple,
    from_global_id_assert_type,
)
from core.graphql.schemas.offer_item import OfferItem
from core.db.models import db
from core.order.order_manager import (
    ACCEPT_ACTION,
    run_order,
)


class ProductOffer(RegisteredUserObjectType):
    class Meta:
        model = ProductOfferModel
        interfaces = (relay.Node,)
        only_fields = (
            'priority',
            'name',
            'offer_items',
            'wine_type',
            'bottle_qty',
            'expert_note',
            'accepted',
            'order',
        )

    product_cost = graphene.Field(graphene.String)
    salestax_cost = graphene.Field(graphene.String)
    shipping_cost = graphene.Field(graphene.String)
    total_cost = graphene.Field(graphene.String)

    @staticmethod
    def get_model_owner(model):
        return model.order.user

    @staticmethod
    def resolve_product_cost(model, info):
        if model.product_cost is None:
            return None
        return str(model.product_cost)

    @staticmethod
    def resolve_salestax_cost(model, info):
        if model.salestax_cost is None:
            return None
        return str(model.salestax_cost)

    @staticmethod
    def resolve_shipping_cost(model, info):
        if model.shipping_cost is None:
            return None
        return str(model.shipping_cost)

    @staticmethod
    def resolve_total_cost(model, info):
        if model.total_cost is None:
            return None
        return str(model.total_cost)

    @staticmethod
    def optimize_resolve_order(query_parent_path):
        from core.graphql.schemas.order import Order
        # TODO solve circular dependency

        query_child_path = '.'.join([query_parent_path, 'order'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=Order
        )

    @staticmethod
    def optimize_resolve_offer_items(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'offer_items'])

        return OptimizeResolveTuple(
            query_options=selectinload(query_child_path),  # TODO figure why this optimization doesn't work
            query_child_path=query_child_path,
            child_node_class=OfferItem
        )


class ProductOfferInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    expert_note = graphene.String()
    salestax_cost = graphene.String()
    shipping_cost = graphene.String()


def save_product_offers(order_inp, order):
    offers_inp = order_inp.get('product_offers')
    if offers_inp is None:
        return

    offer_inp_dict = {}
    for offer_inp in offers_inp:
        product_offer_id = from_global_id_assert_type(offer_inp.id, 'ProductOffer')

        offer_inp_dict[product_offer_id] = offer_inp

    product_offers = ProductOfferModel.query.filter(
        ProductOfferModel.order_id == order.id,
        ProductOfferModel.id.in_(offer_inp_dict.keys())
    )
    for product_offer in product_offers:
        offer_inp = offer_inp_dict[product_offer.id]

        expert_note = offer_inp.get('expert_note')
        if expert_note is not None:
            product_offer.expert_note = expert_note

        costs_updated = False

        salestax_cost_str = offer_inp.get('salestax_cost')
        if salestax_cost_str is not None:
            salestax_cost = Decimal(salestax_cost_str)
            if salestax_cost != product_offer.salestax_cost:
                product_offer.salestax_cost = salestax_cost
                costs_updated = True

        shipping_cost_str = offer_inp.get('shipping_cost')
        if shipping_cost_str is not None:
            shipping_cost = Decimal(shipping_cost_str)
            if shipping_cost != product_offer.shipping_cost:
                product_offer.shipping_cost = shipping_cost
                costs_updated = True

        if costs_updated:
            product_offer.total_cost, product_offer.product_cost = recalc_total_cost(
                product_offer.offer_items, product_offer.salestax_cost, product_offer.shipping_cost
            )


class AcceptProductOffer(relay.ClientIDMutation):
    class Input:
        offer_id = graphene.String(required=True)

    @classmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def mutate_and_get_payload(cls, root, info, identity, offer_id=None):
        logging.info('acceptOffer offer_id: %s', offer_id)
        offer_id = from_global_id_assert_type(offer_id, 'ProductOffer')

        offer = ProductOfferModel.query.get(offer_id)
        order_id = offer.order_id

        # Check permissions
        if identity.id.subject != offer.order.user.cognito_sub:
            raise Exception('PermissionDenied')

        offer.accepted = True
        db.session.commit()

        # Lock money
        run_order(order_id, ACCEPT_ACTION)

        return AcceptProductOffer()
