# pylint: disable=no-member
import logging

from collections import namedtuple

import graphene
from graphene import (
    relay,
    Enum,
)
from graphene.utils.str_converters import to_camel_case
from graphene_sqlalchemy import (
    SQLAlchemyObjectType,
    SQLAlchemyConnectionField,
)
from graphene_sqlalchemy.utils import (
    _symbol_name,
    _ENUM_CACHE,
    EnumValue,
)
from sqlalchemy.inspection import inspect
from graphql.language.ast import (
    FragmentSpread,
    InlineFragment,
)
from graphql_relay.connection.arrayconnection import offset_to_cursor

from core import to_int
from core.cognito import (
    admin_user_permission,
    anonymous_user_permission,
)
from core.db.models import db

OptimizeResolveTuple = namedtuple('OptimizeResolveTuple', [
    'query_options',
    'query_child_path',
    'child_node_class',
])
CustomSortOrder = namedtuple('CustomSortOrder', [
    'name',
    'value',
    'is_asc',
])

SORT_SELECTED_THEMES_SORT_ORDER = 'sort_order'
SORT_SELECTED_THEMES_SELECTED_AT_ASC = 'selected_at_asc'
SORT_SELECTED_THEMES_SELECTED_AT_DESC = 'selected_at_desc'

SelectedThemesSortEnum = graphene.Enum('SelectedThemesSortEnum', [
    (SORT_SELECTED_THEMES_SORT_ORDER, SORT_SELECTED_THEMES_SORT_ORDER),
    (SORT_SELECTED_THEMES_SELECTED_AT_ASC, SORT_SELECTED_THEMES_SELECTED_AT_ASC),
    (SORT_SELECTED_THEMES_SELECTED_AT_DESC, SORT_SELECTED_THEMES_SELECTED_AT_DESC),
])


class ProductReview(graphene.ObjectType):
    reviewer_name = graphene.String()
    review_score = graphene.Int()


def build_product_reviews_cached(model_with_prof_reviews):
    if not hasattr(model_with_prof_reviews, '_product_reviews_cache'):
        if model_with_prof_reviews.prof_reviews:
            try:
                model_with_prof_reviews._product_reviews_cache = [ProductReview(
                    reviewer_name=r.get('name'),
                    review_score=to_int(r.get('score')),
                ) for r in model_with_prof_reviews.prof_reviews]
            except:
                model_with_prof_reviews._product_reviews_cache = []
                logging.exception(
                    'Failed to extract prof_reviews from the following model: %r',
                    model_with_prof_reviews,
                )
        else:
            model_with_prof_reviews._product_reviews_cache = []

    return model_with_prof_reviews._product_reviews_cache


def create_sort_enum_for_model(
        cls, name=None, symbol_name=_symbol_name, custom_sort_orders=(), default_sort_order_name=None
):
    name = name or cls.__name__ + "SortEnum"
    if name in _ENUM_CACHE:
        return _ENUM_CACHE[name][0]

    sort_orders = []
    for column in inspect(cls).columns.values():
        if not default_sort_order_name and column.primary_key:
            default_sort_order_name = symbol_name(column.name, True)
            # TODO account for composite primary keys as well ?
        sort_orders.extend((
            CustomSortOrder(
                name=column.name,
                value=column.asc(),
                is_asc=True,
            ),
            CustomSortOrder(
                name=column.name,
                value=column.desc(),
                is_asc=False,
            ),
        ))
    sort_orders.extend(custom_sort_orders)

    items = []
    default = []
    for sort_order in sort_orders:
        sort_order_name = symbol_name(sort_order.name, sort_order.is_asc)
        enum_value = EnumValue(sort_order_name, sort_order.value)
        if sort_order_name == default_sort_order_name:
            default.append(enum_value)
        items.append((sort_order_name, enum_value))

    enum = Enum(name, items)
    _ENUM_CACHE[name] = (enum, default)
    return enum


def _get_ast_field_dict(ast, fragments):
    ast_field_dict = {}
    if not hasattr(ast, 'selection_set') or not ast.selection_set:
        return ast_field_dict

    for field_ast in ast.selection_set.selections:
        if isinstance(field_ast, InlineFragment):
            for fragment_field_ast in field_ast.selection_set.selections:
                ast_field_dict[fragment_field_ast.name.value] = fragment_field_ast
            continue

        field_name = field_ast.name.value
        if isinstance(field_ast, FragmentSpread):
            for fragment_field_ast in fragments[field_name].selection_set.selections:
                ast_field_dict[fragment_field_ast.name.value] = fragment_field_ast
            continue

        ast_field_dict[field_name] = field_ast

    return ast_field_dict


def _get_optimizer_dict(obj_type):
    optimizer_dict = {}

    optimize_resolve_prefix = 'optimize_resolve_'
    for attr_name in dir(obj_type):
        if not attr_name.startswith(optimize_resolve_prefix):
            continue

        optimizer = getattr(obj_type, attr_name)
        field_snake_case = attr_name[len(optimize_resolve_prefix):]

        if not callable(optimizer) or not field_snake_case:
            continue

        optimizer_dict[to_camel_case(field_snake_case)] = optimizer

    return optimizer_dict


def _optimize_resolve(obj_type, query_options, query_path, ast, fragments):
    optimizer_dict = _get_optimizer_dict(obj_type)
    ast_field_dict = _get_ast_field_dict(ast, fragments)

    for field_name, optimizer in optimizer_dict.items():
        field_ast = ast_field_dict.get(field_name)
        if field_ast is None:
            continue

        optimizer_tuple = optimizer(query_path)
        if optimizer_tuple.query_options:
            if isinstance(optimizer_tuple.query_options, (tuple, list)):
                query_options.extend(optimizer_tuple.query_options)
            else:
                query_options.append(optimizer_tuple.query_options)

        _optimize_resolve(
            optimizer_tuple.child_node_class,
            query_options,
            optimizer_tuple.query_child_path,
            field_ast,
            fragments
        )


def optimize_resolve(obj_type, query, info):
    query_options = []

    if len(info.field_asts) != 1:
        raise ValueError(
            f'len(info.field_asts) expected to be 1 but is {len(info.field_asts)} - investigate why'
        )
    _optimize_resolve(obj_type, query_options, '', info.field_asts[0], info.fragments)
    if query_options:
        query = query.options(*query_options)

    return query


def assert_node_type(node_type, required_type):
    if node_type != required_type:
        raise ValueError(
            "expected id of type '%s' but '%s' received" %
            (required_type, repr(node_type))
        )


def from_global_id_assert_type(global_id, expected_node_type, id_converter=int):
    node_type, node_id = graphene.Node.from_global_id(global_id)
    assert_node_type(node_type, expected_node_type)
    return id_converter(node_id) if id_converter else node_id


class TotalCountConnection(relay.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info):
        return root.length


class OptimizeResolveConnection(TotalCountConnection):
    class Meta:
        abstract = True

    class OptimizeResolveEdges:
        def __init__(self, node_class):
            self._node_class = node_class

        def optimize_resolve_node(self, query_parent_path):
            return OptimizeResolveTuple(
                query_options=None,
                query_child_path=query_parent_path,
                child_node_class=self._node_class
            )

    @classmethod
    def optimize_resolve_edges(cls, query_parent_path):
        return OptimizeResolveTuple(
            query_options=None,
            query_child_path=query_parent_path,
            child_node_class=cls.OptimizeResolveEdges(cls._meta.node)
        )

    @classmethod
    def get_query(cls, info, sort=None, **kwargs):
        model_class = cls._meta.node.get_model_class()
        query = OffsetSQLAlchemyConnectionField.get_query(
            model_class,
            info,
            sort=sort,
            **kwargs
        )
        return optimize_resolve(cls, query, info)


class OptimizeResolveObjectType(SQLAlchemyObjectType):
    class Meta:
        abstract = True

    @classmethod
    def get_model_class(cls):
        return cls._meta.model

    @classmethod
    def get_query(cls, info):
        query = super().get_query(info)
        return optimize_resolve(cls, query, info)


class RegisteredUserObjectType(OptimizeResolveObjectType):
    class Meta:
        abstract = True

    @staticmethod
    def get_model_owner(model):
        return model.user

    @staticmethod
    def is_node_shared(model, owner, identity):
        return False

    @staticmethod
    def is_orphan_node_accessible(model):
        return False

    @classmethod
    def get_node(cls, info, node_id):
        with anonymous_user_permission.require(http_exception=401) as identity:
            model = super().get_node(info, node_id)

            if not model:
                return None

            if admin_user_permission.can():
                return model

            owner = cls.get_model_owner(model)
            if owner:
                if cls.is_node_shared(model, owner, identity):
                    return model
                if identity.id and owner.cognito_sub == identity.id.subject:
                    return model
            elif cls.is_orphan_node_accessible(model):
                return model

            return None


class OffsetSQLAlchemyConnectionField(SQLAlchemyConnectionField):
    def __init__(self, type, *args, **kwargs):
        kwargs.setdefault('offset', graphene.Int())
        super().__init__(type, *args, **kwargs)

    @classmethod
    def resolve_connection(cls, connection_type, model, info, args, resolved):
        offset = args.get('offset')
        if offset is not None:
            args.setdefault('after', offset_to_cursor(offset - 1))
        return super().resolve_connection(connection_type, model, info, args, resolved)


def save_input_field(input_dict, input_key, model, model_attr=None):
    value = input_dict.get(input_key)
    if value is None:
        return False

    if not model_attr:
        model_attr = input_key
    setattr(model, model_attr, value)
    return True


def save_input_fields(input_dict, keys, model):
    updated_keys = set()
    for key in keys:
        if isinstance(key, (tuple, list)):
            is_updated = save_input_field(input_dict, key[0], model, model_attr=key[1])
        else:
            is_updated = save_input_field(input_dict, key, model)

        if is_updated:
            updated_keys.add(key)
    return updated_keys


def save_input_subfields(
        input_dict,
        input_key,
        subkeys,
        model,
        submodel_constructor,
        model_attr=None
):
    created = False
    input_subdict = input_dict.get(input_key)
    if input_subdict is None:
        return created, None

    if not model_attr:
        model_attr = input_key
    submodel = getattr(model, model_attr)

    if not submodel:
        submodel = submodel_constructor()
        setattr(model, model_attr, submodel)
        db.session.add(submodel)
        created = True

    updated_subkeys = save_input_fields(input_subdict, subkeys, submodel)
    return created, submodel, updated_subkeys
