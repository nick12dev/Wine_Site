#
# pylint: disable=unused-argument,too-few-public-methods,no-member
import json
import logging

import graphene
from graphene import relay
from graphene_sqlalchemy import utils
from sqlalchemy.orm import joinedload

from core import config
from core.cognito import (
    registered_user_permission,
    admin_user_permission,
    system_user_permission,
    update_user_from_cognito,
)
from core.cognito_sync import (
    DISABLE_COGNITO_ACTION,
    ENABLE_COGNITO_ACTION,
    FullCognitoUserSync,
    CognitoUserSync,
)
from core.db.models.user import User as UserModel
from core.db.models.user_address import UserAddress as UserAddressModel
from core.db.models.user_card import UserCard as UserCardModel
from core.graphql.data_loaders import (
    get_creator_theme_groups_data_loader,
    get_user_selected_themes_data_loader,
    get_user_selected_theme_groups_data_loader,
)
from core.graphql.schemas.theme import ThemesConnection
from core.graphql.schemas import (
    OffsetSQLAlchemyConnectionField,
    RegisteredUserObjectType,
    save_input_fields,
    save_input_subfields,
    OptimizeResolveConnection,
    OptimizeResolveTuple,
    from_global_id_assert_type,
    SelectedThemesSortEnum,
    SORT_SELECTED_THEMES_SORT_ORDER,
)
from core.graphql.schemas.order import (
    Order,
    OrdersConnection,
)
from core.graphql.schemas.theme_group import ThemeGroupsConnection
from core.graphql.schemas.user_address import (
    UserAddress,
    UserAddressInput,
)
from core.graphql.schemas.user_subscription import (
    UserSubscription,
    UserSubscriptionInput,
)
from core.graphql.schemas.user_card import (
    UserCardsConnection,
    UserCardSortEnum,
    UserCardInput,
    save_user_cards,
)
from core.db.models import db
from core.db.models.order import Order as OrderModel
from core.dbmethods import (
    save_device_token,
    create_order,
)
from core.dbmethods.user import (
    save_stripe_customer_id,
    get_credit_card,
    get_user,
    get_or_create_user,
    get_user_by_sub,
    get_cognito_attr_dict,
    populate_automatic_username,
)
from core.dbmethods.subscription import save_subscription
from core.order.actions.base import send_template_email
from core.order.order_manager import (
    USER_UPCOMING_ORDER_STATES,
    USER_PROPOSED_ORDER_STATES,
    USER_ORDER_HISTORY_STATES,
)

UserSortEnum = utils.sort_enum_for_model(UserModel)


class CreditCard(graphene.ObjectType):
    brand = graphene.String()
    country = graphene.String()
    exp_month = graphene.String()
    exp_year = graphene.String()
    last4 = graphene.String()
    name = graphene.String()


def _can_return_sensitive_info(user, identity):
    return user.cognito_sub == identity.id.subject or identity.can(admin_user_permission)


class User(RegisteredUserObjectType):
    class Meta:
        model = UserModel
        interfaces = (relay.Node,)
        only_fields = (
            'user_number',
            'exists_in_cognito',
            'cognito_enabled',
            'cognito_status',
            'cognito_display_status',
            'cognito_phone_verified',
            'cognito_email_verified',
            'username',
            'username_set_manually',
            'first_name',
            'last_name',
            'email',
            'phone',
            'registration_finished',
            'is_creator',
            'avatar',
            'bio',
            'theme_groups',
            'followed_creators',
            'follower_count',
        )

    selected_themes = OffsetSQLAlchemyConnectionField(
        ThemesConnection,
        sort=graphene.Argument(
            SelectedThemesSortEnum,
            default_value=SORT_SELECTED_THEMES_SORT_ORDER,
        ),
    )
    selected_theme_groups = OffsetSQLAlchemyConnectionField(ThemeGroupsConnection)

    allowed_cognito_actions = graphene.List(graphene.String)
    user_address = graphene.Field(UserAddress)
    user_subscription = graphene.Field(UserSubscription)

    user_cards = OffsetSQLAlchemyConnectionField(
        UserCardsConnection,
        sort=graphene.Argument(
            # graphene.List(
            UserCardSortEnum,
            # ),
            default_value=utils.EnumValue(
                'display_order_asc',
                UserCardModel.display_order.asc()
            )
        )
    )

    proposed_order = graphene.Field(Order)
    upcoming_order = graphene.Field(Order)
    #current_orders = graphene.List(Order)
    current_orders = OffsetSQLAlchemyConnectionField(OrdersConnection)
    all_orders = graphene.List(Order)
    order_history = OffsetSQLAlchemyConnectionField(OrdersConnection)
    credit_card = graphene.Field(CreditCard)

    @staticmethod
    def get_model_owner(model):
        return model

    @staticmethod
    def is_node_shared(model, owner, identity):
        return owner.is_creator or identity.can(registered_user_permission)

    @staticmethod
    def resolve_theme_groups(model, info, sort=None, **kwargs):
        return get_creator_theme_groups_data_loader().load(model.id)

    @staticmethod
    def resolve_selected_themes(model, info, sort=None, **kwargs):
        return get_user_selected_themes_data_loader(sort).load(model.id)

    @staticmethod
    def resolve_selected_theme_groups(model, info, sort=None, **kwargs):
        return get_user_selected_theme_groups_data_loader().load(model.id)

    @staticmethod
    def optimize_resolve_followed_creators(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'followed_creators'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=User
        )

    @staticmethod
    def resolve_allowed_cognito_actions(model, info):
        return [DISABLE_COGNITO_ACTION if model.cognito_enabled else ENABLE_COGNITO_ACTION]

    @staticmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def resolve_credit_card(model, info, identity):
        if not _can_return_sensitive_info(model, identity):
            return None

        card_dct = get_credit_card(model.id)
        if card_dct is None:
            return
        return CreditCard(**card_dct)

    @staticmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def resolve_user_address(model, info, identity):
        if not _can_return_sensitive_info(model, identity):
            return None

        return model.primary_user_address

    @staticmethod
    def optimize_resolve_user_address(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'primary_user_address'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=UserAddress
        )

    @staticmethod
    def resolve_user_subscription(model, info):
        return model.primary_user_subscription

    @staticmethod
    def optimize_resolve_user_subscription(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'primary_user_subscription'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=UserSubscription
        )

    @staticmethod
    def resolve_user_cards(model, info, sort=None, **kwargs):
        return UserCardsConnection.get_query(info, sort=sort, **kwargs).filter(
            UserCardModel.user_id == model.id
        )

    @staticmethod
    def resolve_proposed_order(model, info):
        return db.session.query(OrderModel).filter(
            OrderModel.user_id == model.id,
            OrderModel.state.in_(USER_PROPOSED_ORDER_STATES),
        ).first()

    @staticmethod
    def resolve_upcoming_order(model, info):
        return db.session.query(OrderModel).filter(
            OrderModel.user_id == model.id,
            OrderModel.state.in_(USER_UPCOMING_ORDER_STATES),
        ).first()

    #@staticmethod
    #def resolve_current_orders(model, info):
    #    return db.session.query(OrderModel).filter(
    #        OrderModel.user_id == model.id,
    #        OrderModel.state.in_(USER_PROPOSED_ORDER_STATES + USER_UPCOMING_ORDER_STATES),
    #    ).order_by(OrderModel.state_changed_at.desc())

    @staticmethod
    def resolve_all_orders(model, info):
        return db.session.query(OrderModel).filter(
            OrderModel.user_id == model.id,
        ).order_by(OrderModel.state_changed_at.desc())

    @staticmethod
    def resolve_current_orders(model, info, sort=None, **kwargs):
        return OrdersConnection.get_query(info, sort=None, **kwargs).filter(
            OrderModel.user_id == model.id,
            OrderModel.state.in_(USER_PROPOSED_ORDER_STATES + USER_UPCOMING_ORDER_STATES),
        ).order_by(OrderModel.state_changed_at.desc())


    @staticmethod
    def resolve_order_history(model, info, sort=None, **kwargs):
        return OrdersConnection.get_query(info, sort=None, **kwargs).filter(
            OrderModel.user_id == model.id,
            OrderModel.state.in_(USER_ORDER_HISTORY_STATES),
        ).order_by(OrderModel.state_changed_at.desc())


class UsersConnection(OptimizeResolveConnection):
    class Meta:
        node = User


def _try_to_delete_stale_cognito_user(cognito_sync, user_sub):
    try:
        cognito_user = cognito_sync.get_cognito_user()
        cognito_attrs = get_cognito_attr_dict(cognito_user, attributes_key='UserAttributes')

        if cognito_attrs.get('sub') != user_sub:
            # make sure it is actually a subject (and not an email passed as if it was a subject)
            raise ValueError('Invalid user subject')
        if cognito_user.get('UserStatus', 'UNCONFIRMED') != 'UNCONFIRMED':
            raise ValueError('User should be in UNCONFIRMED state')

        cognito_sync.delete_cognito_user()
    except:
        logging.warning(
            'Failed to get rid of stale Cognito user '
            'upon sign up details update (stale user subject: %s)',
            user_sub,
        )


class SignUp(relay.ClientIDMutation):
    class Input:
        email = graphene.String(required=True)
        phone = graphene.String(required=True)
        password = graphene.String(required=True)
        replace_user_sub = graphene.String()

    user_sub = graphene.String()

    @classmethod
    def mutate_and_get_payload(cls, root, info, **inp):
        user_sub = inp.get('replace_user_sub')
        email = inp['email']
        phone = inp['phone']
        password = inp['password']

        sync = CognitoUserSync(username=user_sub)

        if user_sub:
            _try_to_delete_stale_cognito_user(sync, user_sub)

        try:
            user_sub = sync.sign_up(email, phone, password)
        except BaseException as e:
            error_message = getattr(e, 'response', {}).get('Error', {}).get('Message')
            if error_message:
                raise ValueError(error_message) from e
            raise e
        return SignUp(user_sub=user_sub)


class SaveUser(relay.ClientIDMutation):
    class Input:
        id = graphene.ID()
        cognito_action = graphene.String()
        cognito_phone_verified = graphene.Boolean()
        cognito_email_verified = graphene.Boolean()
        first_name = graphene.String()
        last_name = graphene.String()
        username = graphene.String()
        email = graphene.String()
        phone = graphene.String()
        avatar = graphene.String()
        device_token = graphene.String()
        stripe_token = graphene.String()

        old_password = graphene.String()
        new_password = graphene.String()

        user_address = graphene.InputField(UserAddressInput)
        user_subscription = graphene.InputField(UserSubscriptionInput)
        user_cards = graphene.List(UserCardInput)

    user = graphene.Field(User)

    @classmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def mutate_and_get_payload(cls, root, info, identity, **inp):
        logging.info('saveUser mutation input: %s', inp)

        try:
            global_id = inp['id']
        except KeyError:
            user = get_or_create_user(identity.id.subject)
            is_user_new = not user.registration_finished
        else:
            user_id = from_global_id_assert_type(global_id, 'User')
            user = get_user(user_id)
            is_user_new = False

        if user.cognito_sub == identity.id.subject:
            is_admin_user = admin_user_permission.can()
        else:
            admin_user_permission.test(http_exception=401)
            is_admin_user = True

        old_firstname = user.first_name or ''
        old_lastname = user.last_name or ''
        old_username = user.username or ''
        save_input_fields(
            inp,
            (
                'first_name',
                'last_name',
                'username',
                'avatar',
            ),
            user
        )
        new_firstname = user.first_name or ''
        new_lastname = user.last_name or ''
        new_username = user.username or ''

        if new_username != old_username:
            # TODO otereshchenko: make sure invalid characters are escaped in manual usernames as well
            user.username_set_manually = True

        if new_firstname != old_firstname or new_lastname != old_lastname:
            populate_automatic_username(user)

        # Save address
        save_input_subfields(
            inp,
            'user_address',
            (
                'country',
                'state_region',
                'city',
                'street1',
                'street2',
                'postcode',
            ),
            user,
            lambda: UserAddressModel(user_id=user.id),
            model_attr='primary_user_address'
        )

        # Save subscription
        subscription_inp = inp.get('user_subscription')
        if subscription_inp is not None:
            subscription_inp.produce_budget_decimal()
            subscription = save_subscription(user.id, subscription_inp)
            user.primary_user_subscription_id = subscription.id

        # Save device_token
        device_token_inp = inp.get('device_token')
        if device_token_inp is not None:
            save_device_token(user.id, device_token_inp)

        # Save Stripe customer id
        stripe_token = inp.get('stripe_token')
        if stripe_token is not None:
            save_stripe_customer_id(user.id, stripe_token)

        save_user_cards(inp, user)

        if is_admin_user:
            cognito_user_sync = CognitoUserSync(username=user.cognito_sub)
        else:
            cognito_user_sync = CognitoUserSync(access_token=identity.id.encoded_token)

        cognito_updated = False
        if is_admin_user or not is_user_new:
            cognito_updated = save_cognito_user(cognito_user_sync, inp)

        if cognito_updated or is_user_new:
            try:
                update_user_from_cognito(
                    cognito_user_sync=cognito_user_sync, user=user, clear_missing_data=False
                )
            except:
                logging.exception(
                    'Failed to synchronize a user with id=%s from Cognito to DB!', user.id
                )

        if is_user_new and user.first_name:
            user.registration_finished = True

        db.session.commit()

        return SaveUser(user=user)


def save_cognito_user(cognito_user_sync, inp_dict):
    old_password = inp_dict.get('old_password')
    new_password = inp_dict.get('new_password')

    if new_password:
        if not old_password:
            raise ValueError('Please provide oldPassword together with newPassword')
    elif old_password:
        raise ValueError('In order to change password you need to provide newPassword'
                         ' together with oldPassword')

    cognito_attributes = []
    new_email = inp_dict.get('email')
    if new_email:
        cognito_attributes.append({
            'Name': 'email',
            'Value': new_email,
        })
    new_phone = inp_dict.get('phone')
    if new_phone:
        cognito_attributes.append({
            'Name': 'phone_number',
            'Value': new_phone,
        })
    email_verified = inp_dict.get('cognito_email_verified')
    if email_verified is not None:
        cognito_attributes.append({
            'Name': 'email_verified',
            'Value': str(email_verified).lower(),
        })
    phone_verified = inp_dict.get('cognito_phone_verified')
    if phone_verified is not None:
        cognito_attributes.append({
            'Name': 'phone_number_verified',
            'Value': str(phone_verified).lower(),
        })

    cognito_action = inp_dict.get('cognito_action')

    return cognito_user_sync.update_cognito_user(
        attributes=cognito_attributes,
        old_password=old_password,
        new_password=new_password,
        cognito_action=cognito_action,
    )


class UpdateUserFromCognito(relay.ClientIDMutation):
    class Input:
        lambda_event = graphene.String(required=True)

    @classmethod
    @system_user_permission.require(http_exception=401)
    def mutate_and_get_payload(cls, root, info, lambda_event=None, **kwargs):
        logging.info('UpdateUserFromCognito mutation "lambda_event" input: %r', lambda_event)

        event = json.loads(lambda_event)
        cognito_sub = event['userName']

        update_user_from_cognito(cognito_sub=cognito_sub)

        return UpdateUserFromCognito()


class DoFullCognitoUserSync(relay.ClientIDMutation):
    successfully_updated_count = graphene.Int()
    successfully_added_count = graphene.Int()
    exceptions_count = graphene.Int()
    not_connected_to_cognito_count = graphene.Int()
    not_found_in_cognito_count = graphene.Int()
    cognito_list_complete = graphene.Boolean()

    @classmethod
    @system_user_permission.require(http_exception=401)
    def mutate_and_get_payload(cls, root, info, **inp):
        result = FullCognitoUserSync()().stats_to_dict()
        return DoFullCognitoUserSync(**result)


class PopulateAutomaticUsernames(relay.ClientIDMutation):
    @classmethod
    @system_user_permission.require(http_exception=401)
    def mutate_and_get_payload(cls, root, info, **inp):
        for user in UserModel.query.all():
            populate_automatic_username(user)
        return PopulateAutomaticUsernames()


class UserFilter(graphene.InputObjectType):
    user_number = graphene.Field(graphene.String)
    display_name = graphene.Field(graphene.String)
    cognito_display_status = graphene.Field(graphene.String)


class StartSearch(relay.ClientIDMutation):

    @classmethod
    @registered_user_permission.require(http_exception=401, pass_identity=True)
    def mutate_and_get_payload(cls, root, info, identity, **inp):
        user = get_user_by_sub(identity.id.subject)
        create_order(user.id, user.primary_user_subscription_id)

        try:
            send_template_email(
                user.email, 'welcome',
                {
                    'name': user.first_name or '',
                    'deeplink': config.SERVER_DEEPLINK_URL + '/subscriptions/',
                }
            )
        except Exception as e:
            logging.exception('Error when sending welcome email: %s', e)

        return StartSearch()
