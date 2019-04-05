#
# pylint: disable=too-few-public-methods,unused-argument,invalid-name,no-member
import logging

import graphene
from celery.exceptions import TimeoutError
from graphene import relay
from sqlalchemy.orm import (
    joinedload,
    selectinload,
)

from core.cognito import admin_user_permission
from core.graphql.schemas import (
    OptimizeResolveConnection,
    RegisteredUserObjectType,
    OptimizeResolveTuple,
    create_sort_enum_for_model,
    CustomSortOrder,
    save_input_fields,
    from_global_id_assert_type,
)
from core.graphql.schemas.offer_item import (
    OfferItemReplacementInput,
    replace_offer_items,
)
from core.graphql.schemas.product_offer import (
    ProductOffer,
    save_product_offers,
    ProductOfferInput,
)
from core.graphql.schemas.user_subscription import (
    UserSubscription,
    UserSubscriptionSnapshot,
)
from core.db.models import (
    ORDER_STATES,
    ORDER_ACTIONS,
)
from core.db.models import db
from core.db.models.order import Order as OrderModel
from core.order.order_manager import (
    VALID_MANUAL_STATE_ACTIONS,
    run_order,
    # OrderManager,
)
from core.dbmethods import (
    get_order_tracking_url,
    get_order,
)

OrderSortEnum = create_sort_enum_for_model(OrderModel, custom_sort_orders=[
    CustomSortOrder(name='user_display_name', value=None, is_asc=True),
    CustomSortOrder(name='user_display_name', value=None, is_asc=False),
    CustomSortOrder(name='order_time', value=OrderModel.state_changed_at.asc(), is_asc=True),
    CustomSortOrder(name='order_time', value=OrderModel.state_changed_at.desc(), is_asc=False),
])

OrderStateEnum = graphene.Enum('OrderStateEnum', [
    (state, state) for state in ORDER_STATES.enums
])

OrderActionEnum = graphene.Enum('OrderActionEnum', [
    (action, action) for action in ORDER_ACTIONS.enums
])


class Order(RegisteredUserObjectType):
    class Meta:
        model = OrderModel
        interfaces = (relay.Node,)
        only_fields = (
            'order_number',
            'user',
            'state',
            'state_changed_at',
            'created_at',
            'shipping_name',
            'shipping_street1',
            'shipping_street2',
            'shipping_state_region',
            'shipping_country',
            'shipping_city',
            'shipping_postcode',
            'shipping_phone',
            'shipping_tracking_num',
            'shipping_date',
            'shipping_method',
            'subscription',
            'subscription_snapshot',
            'product_offers',
        )

    state = graphene.Field(OrderStateEnum)
    allowed_actions = graphene.List(OrderActionEnum)
    single_offer = graphene.Field(ProductOffer)
    accepted_offer = graphene.Field(ProductOffer)
    shipping_tracking_url = graphene.String()
    order_time = graphene.types.DateTime()
    is_in_process = graphene.Boolean()

    @staticmethod
    def resolve_is_in_process(model, info):
        return model.is_in_process

    @staticmethod
    def resolve_order_time(model, info):
        return model.state_changed_at

    @staticmethod
    def optimize_resolve_user(query_parent_path):
        from core.graphql.schemas.user import User
        # TODO otereshchenko: better solution for circular dependency problem

        query_child_path = '.'.join([query_parent_path, 'user'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=User
        )

    @staticmethod
    def optimize_resolve_subscription(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'subscription'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=UserSubscription
        )

    @staticmethod
    def optimize_resolve_subscription_snapshot(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'subscription_snapshot'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=UserSubscriptionSnapshot
        )

    @staticmethod
    def optimize_resolve_product_offers(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'product_offers'])

        return OptimizeResolveTuple(
            query_options=selectinload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=ProductOffer
        )

    @staticmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def resolve_allowed_actions(model, info):
        return VALID_MANUAL_STATE_ACTIONS.get(model.state, ())

    @staticmethod
    def resolve_single_offer(model, info):
        try:
            return model.product_offers[0]
        except IndexError:
            return None

    @staticmethod
    def resolve_accepted_offer(model, info):
        try:
            return model.accepted_offers[0]
        except IndexError:
            return None

    @staticmethod
    def optimize_resolve_single_offer(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'product_offers'])

        return OptimizeResolveTuple(
            query_options=selectinload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=ProductOffer
        )

    @staticmethod
    def optimize_resolve_accepted_offer(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'accepted_offers'])

        return OptimizeResolveTuple(
            query_options=selectinload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=ProductOffer
        )

    @staticmethod
    def resolve_shipping_tracking_url(model, info):
        return get_order_tracking_url(model)

    @staticmethod
    def optimize_resolve_shipping_tracking_url(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'shipping_method', 'carrier'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=None
        )


class OrdersConnection(OptimizeResolveConnection):
    class Meta:
        node = Order


# class RunAction(relay.ClientIDMutation):
#     class Input:
#         order_id = graphene.Int()
#         action = graphene.Field(OrderActionEnum)
#
#     @classmethod
#     def mutate_and_get_payload(cls, root, info, **inp):
#         OrderManager(inp['order_id']).run_action(action=inp['action'])
#         return RunAction()


class SaveOrder(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)
        action = graphene.Field(OrderActionEnum)

        shipping_name = graphene.String()
        shipping_street1 = graphene.String()
        shipping_street2 = graphene.String()
        shipping_city = graphene.String()
        shipping_country = graphene.String()
        shipping_state_region = graphene.String()
        shipping_postcode = graphene.String()
        shipping_phone = graphene.String()
        shipping_tracking_num = graphene.String()
        shipping_date = graphene.Date()
        shipping_method_id = graphene.ID()

        product_offers = graphene.List(ProductOfferInput)
        offer_item_replacements = graphene.List(OfferItemReplacementInput)

    order = graphene.Field(Order)

    @classmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def mutate_and_get_payload(cls, root, info, **inp):
        logging.info('SaveOrder input: %s', inp)
        order_id = from_global_id_assert_type(inp['id'], 'Order')

        order = OrderModel.query.get(order_id)

        save_input_fields(
            inp,
            (
                'shipping_name',
                'shipping_street1',
                'shipping_street2',
                'shipping_city',
                'shipping_country',
                'shipping_state_region',
                'shipping_postcode',
                'shipping_phone',
                'shipping_tracking_num',
                'shipping_date',
            ),
            order
        )
        try:
            shipping_method_global_id = inp['shipping_method_id']
        except KeyError:
            pass
        else:
            order.shipping_method_id = from_global_id_assert_type(
                shipping_method_global_id, 'OrderShippingMethod'
            )

        save_product_offers(inp, order)
        replace_offer_items(inp, order)

        db.session.commit()

        order_action = inp.get('action')
        if order_action:
            task_res = run_order.delay(order.id, action=order_action)
            try:
                # wait for the task for up to 10 seconds (some order actions are quick)
                task_res.wait(timeout=10)
            except TimeoutError:
                pass

        db.session.expire_all()
        return SaveOrder(order=get_order(order.id))


class OrderFilter(graphene.InputObjectType):
    order_number = graphene.Field(graphene.String)
    user = graphene.Field(graphene.String)
    state = graphene.Field(OrderStateEnum)
