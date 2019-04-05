# pylint: disable=invalid-name
import graphene

from core.graphql.query import (
    Query,
    Mutation,
)

schema = graphene.Schema(query=Query, mutation=Mutation)
