# pylint: disable=too-few-public-methods,unused-argument
from datetime import datetime
from decimal import Decimal

import graphene
from graphene import relay

from core.graphql.data_loaders import get_subscription_selected_theme_types_data_loader
from core.graphql.schemas import RegisteredUserObjectType
from core.dbmethods import get_current_order
from core.db.models.user_subscription import UserSubscription as UserSubscriptionModel
from core.db.models.user_subscription_snapshot import UserSubscriptionSnapshot as UserSubscriptionSnapshotModel
from core.db.models import (
    SUBSCRIPTION_ACTIVE_STATE,
    SUBSCRIPTION_SUSPENDED_STATE,
)


class SubscriptionState(graphene.Enum):
    active = SUBSCRIPTION_ACTIVE_STATE
    suspended = SUBSCRIPTION_SUSPENDED_STATE


class SubscriptionType(graphene.Enum):
    red = 'red'
    white = 'white'
    mixed = 'mixed'


class UserSubscription(RegisteredUserObjectType):
    class Meta:
        model = UserSubscriptionModel
        interfaces = (relay.Node,)
        only_fields = ('bottle_qty', 'state')

    type = graphene.Field(SubscriptionType)
    budget = graphene.String()
    month_to_process = graphene.Int()
    order_month_time = graphene.types.datetime.DateTime()
    order_is_in_process = graphene.Boolean()
    order_is_active = graphene.Boolean()  # Order is in states before Accepted by User
    red_themes_selected = graphene.Boolean()
    white_themes_selected = graphene.Boolean()

    @staticmethod
    def resolve_type(model, info):
        if model.type is None:
            return None
        try:
            return SubscriptionType.get(model.type)
        except ValueError:
            return None

    @staticmethod
    def resolve_budget(model, info):
        if model.budget is None:
            return None
        return str(model.budget)

    @staticmethod
    def resolve_month_to_process(model, info):
        order = _get_current_order_cached(model)
        if order is None:
            return datetime.utcnow().month
        return order.month

    @staticmethod
    def resolve_order_month_time(model, info):
        order = _get_current_order_cached(model)
        if order is None:
            return None
        return order.month_time

    @staticmethod
    def resolve_order_is_in_process(model, info):
        order = _get_current_order_cached(model)
        if order is None:
            return False
        return order.is_in_process

    @staticmethod
    def resolve_order_is_active(model, info):
        order = _get_current_order_cached(model)
        if order is None:
            return False
        return order.is_active

    @staticmethod
    def resolve_red_themes_selected(model, info):
        return _is_theme_type_selected_promise(model.id, SubscriptionType.red.value)

    @staticmethod
    def resolve_white_themes_selected(model, info):
        return _is_theme_type_selected_promise(model.id, SubscriptionType.white.value)


def _is_theme_type_selected_promise(subscription_id, theme_type):
    return get_subscription_selected_theme_types_data_loader().load(
        subscription_id
    ).then(did_fulfill=lambda wine_types: theme_type in wine_types)


def _get_current_order_cached(model):
    if not hasattr(model, '_current_order_cache'):
        model._current_order_cache = get_current_order(model.user.id)
    return model._current_order_cache


class UserSubscriptionSnapshot(RegisteredUserObjectType):
    class Meta:
        model = UserSubscriptionSnapshotModel
        interfaces = (relay.Node,)
        only_fields = ('bottle_qty',)

    type = graphene.Field(SubscriptionType)
    budget = graphene.String()

    @staticmethod
    def resolve_type(model, info):
        if model.type is None:
            return None
        try:
            return SubscriptionType.get(model.type)
        except ValueError:
            return None

    @staticmethod
    def resolve_budget(model, info):
        if model.budget is None:
            return None
        return str(model.budget)


class UserSubscriptionInput(graphene.InputObjectType):
    state = graphene.Field(SubscriptionState)
    type = graphene.Field(SubscriptionType)
    bottle_qty = graphene.Int()
    budget = graphene.String()
    apply_for_current_order = graphene.Boolean(default=False)

    def produce_budget_decimal(self):
        # pylint: disable=unsubscriptable-object,unsupported-assignment-operation
        try:
            budget = self['budget']
            self['budget_decimal'] = None if budget is None else Decimal(budget)
        except KeyError:
            return
