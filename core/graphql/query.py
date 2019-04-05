# pylint: disable=unused-argument,too-few-public-methods
from datetime import datetime

import graphene
from flask import current_app
from graphene_sqlalchemy import utils

from core.db.models.domain_card import DomainCard as DomainCardModel
from core.db.models.theme import Theme as ThemeModel
from core.db.models.theme_group import ThemeGroup as ThemeGroupModel
from core.dbmethods.user import (
    get_user_by_sub,
    get_user_by_username,
)
from core.graphql.schemas.order import (
    SaveOrder,
    # RunAction,
)
from core.graphql.schemas.pipeline_sequence import (
    RunPipelineSequence,
    SavePipelineSequence,
    SavePipelineSchedules,
)
from core.graphql.schemas.product_offer import AcceptProductOffer
from core.graphql.schemas.theme import (
    ThemesConnection,
    SetUserThemeSelections,
)
from core.graphql.schemas.theme_group import ThemeGroupsConnection
from core.graphql.schemas.user import (
    User,
    SaveUser,
    DoFullCognitoUserSync,
    UpdateUserFromCognito,
    StartSearch,
    SignUp,
    PopulateAutomaticUsernames,
)
from core.graphql.schemas.domain_card import (
    DomainCardsConnection,
    DomainCardSortEnum,
)
from core.graphql.schemas import OffsetSQLAlchemyConnectionField
from core.graphql.schemas.management import (
    UserManagement,
    OrderManagement,
    ScheduleManagement,
)
from core.cognito import (
    registered_user_permission,
    admin_user_permission,
    system_user_permission,
)


class Query(graphene.ObjectType):
    node = graphene.Node.Field()

    current_time_loc = graphene.DateTime()
    current_time_utc = graphene.DateTime()

    domain_cards = OffsetSQLAlchemyConnectionField(
        DomainCardsConnection,
        sort=graphene.Argument(
            # graphene.List(
            DomainCardSortEnum,
            # ),
            default_value=utils.EnumValue(
                'display_order_asc',
                DomainCardModel.display_order.asc()
            )
        )
    )

    themes = OffsetSQLAlchemyConnectionField(ThemesConnection)
    theme_groups = OffsetSQLAlchemyConnectionField(ThemeGroupsConnection)

    user = graphene.Field(User)
    creator = graphene.Field(User, username=graphene.Argument(graphene.String, required=True))

    user_management = graphene.Field(UserManagement)
    order_management = graphene.Field(OrderManagement)
    schedule_management = graphene.Field(ScheduleManagement)

    @staticmethod
    @system_user_permission.require(http_exception=401)
    def resolve_current_time_loc(_, info):
        # convenience method to check what time it is on the server (local timezone)
        return datetime.now()

    @staticmethod
    @system_user_permission.require(http_exception=401)
    def resolve_current_time_utc(_, info):
        # convenience method to check what time it is on the server (utc timezone)
        return datetime.utcnow()

    @staticmethod
    def resolve_domain_cards(_, info, sort=None, **kwargs):
        return DomainCardsConnection.get_query(
            info,
            sort=sort,
            **kwargs
        ).filter(
            DomainCardModel.category_id == current_app.config['M3_DOMAIN_CATEGORY_ID']
        )

    @staticmethod
    def resolve_themes(_, info, sort=None, **kwargs):
        return ThemesConnection.get_query(
            info,
            sort=None,
            **kwargs
        ).outerjoin(
            ThemeModel.theme_group
        ).filter(
            ThemeGroupModel.is_active != False
        ).order_by(
            ThemeGroupModel.is_promoted.desc(),
            ThemeGroupModel.sort_order.asc(),
            ThemeGroupModel.title.asc(),
            ThemeModel.sort_order.asc(),
            ThemeModel.title.asc(),
        )

    @staticmethod
    def resolve_theme_groups(_, info, sort=None, **kwargs):
        return ThemeGroupsConnection.get_query(
            info,
            sort=None,
            **kwargs
        ).join(
            ThemeGroupModel.themes
        ).filter(
            ThemeGroupModel.is_active != False
        ).order_by(
            ThemeGroupModel.is_promoted.desc(),
            ThemeGroupModel.sort_order.asc(),
            ThemeGroupModel.title.asc(),
        )

    @staticmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def resolve_user(_, info, identity):
        return get_user_by_sub(identity.id.subject)

    @staticmethod
    def resolve_creator(_, info, username=None):
        user = get_user_by_username(username)
        if not user.is_creator:
            registered_user_permission.test()
        return user

    @staticmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def resolve_user_management(_, info):
        return UserManagement()

    @staticmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def resolve_order_management(_, info):
        return OrderManagement()

    @staticmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def resolve_schedule_management(_, info):
        return ScheduleManagement()


class Mutation(graphene.ObjectType):
    sign_up = SignUp.Field()
    save_user = SaveUser.Field()
    update_user_from_cognito = UpdateUserFromCognito.Field()
    do_full_cognito_user_sync = DoFullCognitoUserSync.Field()
    populate_automatic_usernames = PopulateAutomaticUsernames.Field()
    save_order = SaveOrder.Field()
    set_user_theme_selections = SetUserThemeSelections.Field()
    accept_offer = AcceptProductOffer.Field()
    run_pipeline_sequence = RunPipelineSequence.Field()
    save_pipeline_sequence = SavePipelineSequence.Field()
    save_pipeline_schedules = SavePipelineSchedules.Field()
    start_search = StartSearch.Field()
    # run_action = RunAction.Field()
