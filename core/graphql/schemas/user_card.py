# ...blank comment... ("pylint: disable" is ignored for some reason when it goes as the first line in this file)
# pylint: disable=too-few-public-methods,unused-argument,no-member,invalid-name
from flask import current_app
import graphene
from graphene import relay
from graphene_sqlalchemy import utils
from sqlalchemy.orm import joinedload

from core.db.models import db
from core.db.models.domain_card import DomainCard as DomainCardModel
from core.db.models.user_card import UserCard as UserCardModel
from core.graphql.schemas import (
    RegisteredUserObjectType,
    OptimizeResolveConnection,
    OptimizeResolveTuple,
    from_global_id_assert_type,
)
from core.graphql.schemas.domain_card import DomainCard


class CardPreference(graphene.Enum):
    like = 1
    neutral = 0
    dislike = -1


class UserCard(RegisteredUserObjectType):
    class Meta:
        model = UserCardModel
        interfaces = (relay.Node,)
        only_fields = ('display_order',)

    preference = graphene.Field(CardPreference)
    domain_card_id = graphene.ID()
    domain_card = graphene.Field(DomainCard)

    @staticmethod
    def resolve_preference(model, info):
        if model.value is None:
            return None
        try:
            return CardPreference.get(round(model.value))
        except ValueError:
            return None

    @staticmethod
    def resolve_domain_card_id(model, info):
        return graphene.Node.to_global_id('DomainCard', model.card_id)

    @staticmethod
    def resolve_domain_card(model, info):
        return model.card

    @staticmethod
    def optimize_resolve_domain_card(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'card'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=DomainCard
        )


class UserCardsConnection(OptimizeResolveConnection):
    class Meta:
        node = UserCard


UserCardSortEnum = utils.sort_enum_for_model(UserCardModel)


class UserCardInput(graphene.InputObjectType):
    domain_card_id = graphene.ID(required=True)
    preference = graphene.Field(CardPreference, required=True)


def save_user_cards(inp, user):
    cards_inp = inp.get('user_cards')
    if cards_inp is None:
        return

    card_inp_dict = {}
    for card_inp in cards_inp:
        domain_card_id = from_global_id_assert_type(card_inp.domain_card_id, 'DomainCard')

        if domain_card_id in card_inp_dict:
            raise ValueError('UserCard.domainCardId: duplicate entry for ' + repr(card_inp.domain_card_id))

        card_inp_dict[domain_card_id] = card_inp

    domain_cards = DomainCardModel.query.filter(DomainCardModel.id.in_(card_inp_dict.keys()))
    domain_card_dict = {domain_card.id: domain_card for domain_card in domain_cards}

    existing_user_cards = UserCardModel.query.filter(
        UserCardModel.user_id == user.id
    ).filter(UserCardModel.card_id.in_(card_inp_dict.keys()))

    existing_user_card_dict = {}
    for user_card in existing_user_cards:
        try:
            duplicated_user_card = existing_user_card_dict[user_card.card_id]
        except KeyError:
            existing_user_card_dict[user_card.card_id] = user_card
        else:
            current_app.logger.warning(
                "Duplicate user card found in the database. Deleting..."
                " (user id=%(user_id)d; domain card id=%(domain_card_id)d;"
                " user card id being deleted=%(deleted_user_card_id)d;"
                " user card id that will be used instead=%(user_card_id)d)",
                {
                    'user_id': user.id,
                    'domain_card_id': user_card.card_id,
                    'deleted_user_card_id': user_card.id,
                    'user_card_id': duplicated_user_card.id,
                }
            )
            db.session.delete(user_card)

    _add_update_user_cards(card_inp_dict, domain_card_dict, existing_user_card_dict, user)


def _add_update_user_cards(card_inp_dict, domain_card_dict, existing_user_card_dict, user):
    for domain_card_id, card_inp in card_inp_dict.items():
        try:
            domain_card = domain_card_dict[domain_card_id]
        except KeyError:
            current_app.logger.warning(
                "Attempt to save user card for a non-existing domain card. Skipping..."
                " (user id=%(user_id)d; non-existing domain card id=%(domain_card_id)d)",
                {
                    'user_id': user.id,
                    'domain_card_id': domain_card_id,
                }
            )
        else:
            try:
                user_card = existing_user_card_dict[domain_card_id]
            except KeyError:
                user_card = UserCardModel(user_id=user.id, card_id=domain_card_id)
                db.session.add(user_card)

            user_card.display_order = domain_card.display_order
            user_card.value = card_inp.preference
            user_card.preference = CardPreference.get(card_inp.preference).name
