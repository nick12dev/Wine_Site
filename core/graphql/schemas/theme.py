# pylint: disable=fixme,too-few-public-methods,no-member
import logging

import graphene
from graphene import relay
from sqlalchemy.orm import joinedload

from core.cognito import (
    registered_user_permission,
    anonymous_user_permission,
)
from core.db.models import db
from core.db.models.user import (
    User as UserModel,
    user_creators_table,
)
from core.db.models.theme_group import ThemeGroup as ThemeGroupModel
from core.db.models.theme import Theme as ThemeModel
from core.dbmethods.user import get_or_create_user
from core.graphql.data_loaders import (
    get_theme_is_selected_data_loader,
    get_theme_example_wines_data_loader,
)
from core.graphql.schemas.theme_example_wine import ThemesExampleWinesConnection
from core.graphql.schemas.theme_group import ThemeGroup
from core.graphql.schemas import (
    OptimizeResolveObjectType,
    OptimizeResolveConnection,
    OptimizeResolveTuple,
    OffsetSQLAlchemyConnectionField,
    from_global_id_assert_type,
)
from core.graphql.schemas.user_subscription import SubscriptionType


class ContentBlock(graphene.ObjectType):
    image = graphene.String()
    text = graphene.String()


class Theme(OptimizeResolveObjectType):
    class Meta:
        model = ThemeModel
        interfaces = (relay.Node,)
        only_fields = (
            'theme_group',
            'title',
            'image',
            'short_description',
            'sort_order',
        )

    is_selected = graphene.Boolean()
    content_blocks = graphene.List(ContentBlock)
    example_wines = OffsetSQLAlchemyConnectionField(ThemesExampleWinesConnection)
    wine_types = graphene.List(graphene.String)
    is_red_theme = graphene.Boolean()
    is_white_theme = graphene.Boolean()

    @staticmethod
    @anonymous_user_permission.require(http_exception=401, pass_identity=True)
    def resolve_is_selected(model, info, identity):
        if identity.id:
            return get_theme_is_selected_data_loader(identity.id.subject).load(model.id)
        return False

    @staticmethod
    def resolve_example_wines(model, info, **kwargs):
        return get_theme_example_wines_data_loader().load(model.id)

    @staticmethod
    def resolve_content_blocks(model, info):
        if not model.content_blocks:
            return []

        blocks = []
        try:
            for block in model.content_blocks:
                image = block.get('image')
                text = block.get('text')
                if image or text:
                    blocks.append(ContentBlock(
                        image=image,
                        text=text,
                    ))
        except:
            logging.exception('Failed to unpack content_blocks of Theme with id=%s', model.id)
        return blocks

    @staticmethod
    def optimize_resolve_theme_group(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'theme_group'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=ThemeGroup
        )

    @staticmethod
    def resolve_is_red_theme(model, info):
        return SubscriptionType.red.value in model.wine_types

    @staticmethod
    def resolve_is_white_theme(model, info):
        return SubscriptionType.white.value in model.wine_types


class ThemesConnection(OptimizeResolveConnection):
    class Meta:
        node = Theme


class ThemeSelectionInput(graphene.InputObjectType):
    theme_id = graphene.ID(required=True)
    selected = graphene.Boolean(required=True)


class SetUserThemeSelections(relay.ClientIDMutation):
    class Input:
        theme_selections = graphene.List(ThemeSelectionInput, required=True)

    @classmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def mutate_and_get_payload(cls, root, info, identity, theme_selections=()):
        logging.info('setUserThemeSelections: theme_selections=%s', theme_selections)

        selection_inp_dict = {}
        for selection_inp in theme_selections:
            theme_id = from_global_id_assert_type(selection_inp.theme_id, 'Theme')

            if theme_id in selection_inp_dict:
                raise ValueError(
                    'input.themeSelections.theme_id: duplicate entry for ' +
                    repr(selection_inp.theme_id)
                )

            selection_inp_dict[theme_id] = selection_inp

        user = get_or_create_user(identity.id.subject)

        themes = ThemeModel.query.filter(
            ThemeModel.id.in_(selection_inp_dict.keys())
        ).options(
            joinedload(ThemeModel.theme_group),
            joinedload('theme_group.user'),
        )

        creators = {}
        for theme in themes:
            creators[theme.theme_group.user.id] = theme.theme_group.user

            selection_inp = selection_inp_dict[theme.id]
            if selection_inp.selected:
                user.selected_themes.append(theme)
            else:
                try:
                    user.selected_themes.remove(theme)
                except ValueError:
                    pass

        db.session.flush()

        for creator in creators.values():
            following_exists = db.session.query(
                UserModel.query.join(
                    UserModel.selected_themes
                ).join(
                    ThemeModel.theme_group
                ).filter(
                    UserModel.id == user.id,
                    ThemeGroupModel.user_id == creator.id,
                ).exists()
            ).scalar()

            if following_exists:
                user.followed_creators.append(creator)
            else:
                user.followed_creators.remove(creator)

        db.session.flush()

        for creator in creators.values():
            creator.follower_count = db.session.query(user_creators_table).filter(
                user_creators_table.c.creator_id == creator.id
            ).count()

        db.session.commit()

        return SetUserThemeSelections()
