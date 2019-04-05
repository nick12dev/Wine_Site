# pylint: disable=fixme
import graphene
from graphene import relay
from sqlalchemy.orm import (
    joinedload,
    selectinload,
)

from core.cognito import registered_user_permission
from core.db.models.theme_group import ThemeGroup as ThemeGroupModel
from core.graphql.data_loaders import get_theme_group_selected_themes_data_loader
from core.graphql.schemas import (
    OptimizeResolveObjectType,
    OptimizeResolveConnection,
    OptimizeResolveTuple,
)


class ThemeGroup(OptimizeResolveObjectType):
    class Meta:
        model = ThemeGroupModel
        interfaces = (relay.Node,)
        only_fields = (
            'user',
            'sort_order',
            'is_active',
            'is_promoted',
            'title',
            'description',
            'themes',
        )

    selected_themes = graphene.List('core.graphql.schemas.theme.Theme')

    @staticmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def resolve_selected_themes(model, info, identity):
        return get_theme_group_selected_themes_data_loader(identity.id.subject).load(model.id)

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
    def optimize_resolve_themes(query_parent_path):
        from core.graphql.schemas.theme import Theme
        # TODO otereshchenko: better solution for circular dependency problem

        query_child_path = '.'.join([query_parent_path, 'themes'])

        return OptimizeResolveTuple(
            query_options=selectinload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=Theme,
        )


class ThemeGroupsConnection(OptimizeResolveConnection):
    class Meta:
        node = ThemeGroup
