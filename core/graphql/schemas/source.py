# pylint: disable=unused-import,line-too-long
from graphene import relay

from core.graphql.schemas import RegisteredUserObjectType
from core.db.models.source import Source as SourceModel


class Source(RegisteredUserObjectType):
    class Meta:
        model = SourceModel
        interfaces = (relay.Node,)
        only_fields = (
            'name',
        )

    @staticmethod
    def get_model_owner(model):
        return None
