# pylint: disable=unused-import,line-too-long
from graphene import relay

from core.graphql.schemas import RegisteredUserObjectType
from core.db.models.order_shipping_method import OrderShippingMethod as OrderShippingMethodModel

# TODO sqlalchemy mapper fails if these import are not here... put a complete list of model imports into __init__.py ?
from core.db.models.user_subscription import UserSubscription as UserSubscriptionModel
from core.db.models.order import Order as OrderModel
from core.db.models.product_offer import ProductOffer as ProductOfferModel
from core.db.models.user import User as UserModel


class OrderShippingMethod(RegisteredUserObjectType):
    class Meta:
        model = OrderShippingMethodModel
        interfaces = (relay.Node,)
        only_fields = (
            'name',
        )

    @staticmethod
    def get_model_owner(model):
        return None
