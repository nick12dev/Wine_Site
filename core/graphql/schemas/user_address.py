import graphene
from graphene import relay
from core.db.models.user_address import UserAddress as UserAddressModel
from core.graphql.schemas import RegisteredUserObjectType


class UserAddress(RegisteredUserObjectType):
    class Meta:
        model = UserAddressModel
        interfaces = (relay.Node,)
        only_fields = ('country', 'state_region', 'city', 'street1', 'street2', 'postcode')


class UserAddressInput(graphene.InputObjectType):
    country = graphene.String()
    state_region = graphene.String()
    city = graphene.String()
    street1 = graphene.String()
    street2 = graphene.String()
    postcode = graphene.String()
