# pylint: disable=too-few-public-methods
from graphene import relay
from graphene_sqlalchemy import utils
from core.db.models.domain_card import DomainCard as DomainCardModel
from core.graphql.schemas import (
    OptimizeResolveObjectType,
    OptimizeResolveConnection,
)


class DomainCard(OptimizeResolveObjectType):
    class Meta:
        model = DomainCardModel
        interfaces = (relay.Node,)
        only_fields = ('display_title', 'display_text', 'display_image', 'display_order')

    @staticmethod
    def resolve_display_image(model, info):
        value = model.display_image
        return value.strip() if value else value


class DomainCardsConnection(OptimizeResolveConnection):
    class Meta:
        node = DomainCard


DomainCardSortEnum = utils.sort_enum_for_model(DomainCardModel)
