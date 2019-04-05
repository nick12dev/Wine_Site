#
# pylint: disable=unused-argument,fixme
import graphene
from graphene_sqlalchemy import utils
from sqlalchemy import or_

from core.graphql.schemas import (
    OffsetSQLAlchemyConnectionField,
)
from core.graphql.schemas.order import (
    OrdersConnection,
    OrderFilter,
    OrderStateEnum,
    OrderSortEnum,
)
from core.graphql.schemas.order_shipping_method import OrderShippingMethod
from core.graphql.schemas.pipeline_sequence import (
    PipelineSequencesConnection,
    PipelineSequenceSortEnum,
)
from core.graphql.schemas.user import (
    UsersConnection,
    UserFilter,
    UserSortEnum,
)
from core.db.models import (
    db,
    ORDER_STATES,
)
from core.db.models.user import User as UserModel
from core.db.models.order import Order as OrderModel
from core.db.models.order_shipping_method import OrderShippingMethod as OrderShippingMethodModel
from core.db.models.pipeline_sequence import PipelineSequence as PipelineSequenceModel
from core.db.models.source import Source as SourceModel


class UserManagement(graphene.ObjectType):
    users = OffsetSQLAlchemyConnectionField(
        UsersConnection,
        list_filter=graphene.Argument(UserFilter),
        sort=graphene.Argument(
            graphene.List(UserSortEnum),
            default_value=utils.EnumValue(
                'user_number_asc',
                UserModel.user_number.asc()
            )
        )
    )
    cognito_display_statuses = graphene.List(graphene.String)

    @staticmethod
    def resolve_users(_, info, sort=None, list_filter=None, **kwargs):
        query = UsersConnection.get_query(info, sort=sort, **kwargs)
        if list_filter:
            if list_filter.user_number:
                query = query.filter(
                    UserModel.user_number.ilike(f'%{list_filter.user_number}%')
                )
            if list_filter.display_name:
                # TODO introduce real users.display_name column to the db
                query = query.filter(
                    UserModel.first_name.ilike(f'%{list_filter.display_name}%')
                )
            if list_filter.cognito_display_status:
                if list_filter.cognito_display_status == 'UNKNOWN':
                    query = query.filter(
                        or_(
                            UserModel.cognito_display_status == None,
                            UserModel.cognito_display_status == 'UNKNOWN',
                        )
                    )
                else:
                    query = query.filter(
                        UserModel.cognito_display_status == list_filter.cognito_display_status
                    )
        return query

    @staticmethod
    def resolve_cognito_display_statuses(_, info):
        # TODO support as enum in code ?
        query = db.session.query(
            UserModel.cognito_display_status
        ).distinct().order_by(
            UserModel.cognito_display_status.asc()
        )
        return [row[0] if row[0] else 'UNKNOWN' for row in query]


class OrderManagement(graphene.ObjectType):
    orders = OffsetSQLAlchemyConnectionField(
        OrdersConnection,
        list_filter=graphene.Argument(OrderFilter),
        sort=graphene.Argument(
            # graphene.List(
            OrderSortEnum,
            # ),
            default_value=OrderSortEnum.order_time_desc.value
        )
    )
    order_states = graphene.List(OrderStateEnum)
    shipping_methods = graphene.List(OrderShippingMethod)

    @staticmethod
    def resolve_orders(_, info, sort=None, list_filter=None, **kwargs):
        if sort in ('user_display_name_asc', 'user_display_name_desc'):
            query = OrdersConnection.get_query(info, **kwargs).join(OrderModel.user)
            if sort.endswith('_asc'):
                query = query.order_by(
                    UserModel.first_name.asc(),
                    OrderModel.id.asc(),
                )
            else:
                query = query.order_by(
                    UserModel.first_name.desc(),
                    OrderModel.id.desc(),
                )
        else:
            query = OrdersConnection.get_query(info, sort=sort, **kwargs)

        if list_filter:
            if list_filter.order_number:
                query = query.filter(OrderModel.order_number.ilike(f'%{list_filter.order_number}%'))
            if list_filter.user:
                query = query.join(OrderModel.user).filter(
                    UserModel.first_name.ilike(f'%{list_filter.user}%')
                )
            if list_filter.state:
                query = query.filter(OrderModel.state == list_filter.state)
        return query

    @staticmethod
    def resolve_order_states(_, info):
        # TODO most common states should be at the top
        return [OrderStateEnum.get(state) for state in ORDER_STATES.enums]

    @staticmethod
    def resolve_shipping_methods(_, info):
        return OrderShippingMethodModel.query.order_by(OrderShippingMethodModel.name.asc())


class ScheduleManagement(graphene.ObjectType):
    pipeline_sequences = OffsetSQLAlchemyConnectionField(
        PipelineSequencesConnection,
        sort=graphene.Argument(
            graphene.List(PipelineSequenceSortEnum),
            default_value=utils.EnumValue(
                'source_name_asc',
                None
            )
        )
    )

    @staticmethod
    def resolve_pipeline_sequences(_, info, sort=None, **kwargs):
        if sort in ('source_name_asc', 'source_name_desc'):
            query = PipelineSequencesConnection.get_query(info, **kwargs).join(
                PipelineSequenceModel.source
            )
            if sort.endswith('_asc'):
                query = query.order_by(
                    SourceModel.name.asc(),
                    PipelineSequenceModel.id.asc(),
                )
            else:
                query = query.order_by(
                    SourceModel.name.desc(),
                    PipelineSequenceModel.id.desc(),
                )
        else:
            query = PipelineSequencesConnection.get_query(info, sort=sort, **kwargs)
        return query
