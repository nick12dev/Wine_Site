# pylint: disable=unused-argument,protected-access
import graphene
from graphene import relay
from sqlalchemy.orm import joinedload

from core.db.models.theme_example_wine import ThemeExampleWine as ThemeExampleWineModel
from core.graphql.schemas import (
    OptimizeResolveObjectType,
    OptimizeResolveConnection,
    ProductReview,
    build_product_reviews_cached,
    OptimizeResolveTuple,
)


class ThemeExampleWine(OptimizeResolveObjectType):
    class Meta:
        model = ThemeExampleWineModel
        interfaces = (relay.Node,)
        only_fields = (
            'theme',
            'brand',
            'name',
            'score_num',
            'image',
            'description',
            'sort_order',
            'location',
            'highlights',
            'varietals',
            'qty',
            'sku',
            'qoh',
            'product_url',
        )

    price = graphene.Field(graphene.String)
    msrp = graphene.Field(graphene.String)
    highlights = graphene.List(graphene.String)
    varietals = graphene.List(graphene.String)

    product_reviews = graphene.List(ProductReview)
    top_product_review = graphene.Field(ProductReview)

    @staticmethod
    def optimize_resolve_theme(query_parent_path):
        from core.graphql.schemas.theme import Theme
        # TODO otereshchenko: better solution for circular dependency problem

        query_child_path = '.'.join([query_parent_path, 'theme'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=Theme
        )

    @staticmethod
    def resolve_price(model, info):
        if model.price is not None:
            return str(model.price)

    @staticmethod
    def resolve_msrp(model, info):
        if model.msrp is not None:
            return str(model.msrp)

    @staticmethod
    def resolve_product_reviews(model, info):
        return build_product_reviews_cached(model)

    @staticmethod
    def resolve_top_product_review(model, info):
        reviews = build_product_reviews_cached(model)
        if reviews:
            return reviews[0]


class ThemesExampleWinesConnection(OptimizeResolveConnection):
    class Meta:
        node = ThemeExampleWine
