# pylint: disable=no-member
from collections import defaultdict

from flask import g
from promise import Promise
from promise.dataloader import DataLoader

from core.db.models import db
from core.db.models.theme import Theme
from core.db.models.theme_example_wine import ThemeExampleWine
from core.db.models.theme_group import ThemeGroup
from core.db.models.user import (
    user_themes_table,
    User,
)
from core.db.models.user_subscription import UserSubscription
from core.graphql.schemas import (
    SORT_SELECTED_THEMES_SELECTED_AT_ASC,
    SORT_SELECTED_THEMES_SELECTED_AT_DESC,
)


def get_theme_is_selected_data_loader(cognito_sub):
    return get_data_loader(
        (get_theme_is_selected_data_loader, cognito_sub),

        db.session.query(user_themes_table.c.theme_id).join(
            User, User.id == user_themes_table.c.user_id
        ).filter(
            User.cognito_sub == cognito_sub,
        ),

        user_themes_table.c.theme_id,
        get_row_key=lambda r: r.theme_id,
        rows_to_value=bool,
    )


def get_subscription_selected_theme_types_data_loader():
    def _rows_to_value(r_list):
        wine_types = {wt for r in r_list for wt in r[0]}
        return {wt.lower() for wt in wine_types}

    return get_data_loader(
        get_subscription_selected_theme_types_data_loader,

        db.session.query(Theme.wine_types, UserSubscription.id).join(
            Theme.users_who_selected
        ).join(
            UserSubscription, UserSubscription.user_id == User.id
        ).join(
            Theme.theme_group
        ).filter(
            ThemeGroup.is_active != False,
        ),

        UserSubscription.id,
        get_row_key=lambda r: r[1],
        rows_to_value=_rows_to_value,
    )


def get_theme_example_wines_data_loader():
    return get_data_loader(
        get_theme_example_wines_data_loader,

        ThemeExampleWine.query.order_by(
            ThemeExampleWine.theme_id.asc(),
            ThemeExampleWine.sort_order.asc(),
            ThemeExampleWine.name.asc(),
        ),

        ThemeExampleWine.theme_id,
        get_row_key=lambda r: r.theme_id,
    )


def get_creator_theme_groups_data_loader():
    return get_data_loader(
        get_creator_theme_groups_data_loader,

        ThemeGroup.query.join(
            ThemeGroup.themes,
        ).filter(
            ThemeGroup.is_active != False,
        ).order_by(
            ThemeGroup.is_promoted.desc(),
            ThemeGroup.sort_order.asc(),
            ThemeGroup.title.asc(),
        ),

        ThemeGroup.user_id,
        get_row_key=lambda r: r.user_id,
    )


def get_user_selected_themes_data_loader(sort):
    query = db.session.query(Theme, User.id).join(
        user_themes_table, user_themes_table.c.theme_id == Theme.id
    ).join(
        User, User.id == user_themes_table.c.user_id
    ).join(
        Theme.theme_group
    ).filter(
        ThemeGroup.is_active != False,
    )
    if sort == SORT_SELECTED_THEMES_SELECTED_AT_ASC:
        query = query.order_by(
            user_themes_table.c.selected_at.asc(),
        )
    elif sort == SORT_SELECTED_THEMES_SELECTED_AT_DESC:
        query = query.order_by(
            user_themes_table.c.selected_at.desc(),
        )
    else:
        query = query.order_by(
            ThemeGroup.is_promoted.desc(),
            ThemeGroup.sort_order.asc(),
            ThemeGroup.title.asc(),
            Theme.sort_order.asc(),
            Theme.title.asc(),
        )

    return get_data_loader(
        (get_user_selected_themes_data_loader, sort),

        query,

        User.id,
        get_row_key=lambda r: r[1],
        rows_to_value=lambda r_list: [r[0] for r in r_list],
    )


def get_user_selected_theme_groups_data_loader():
    return get_data_loader(
        get_user_selected_theme_groups_data_loader,

        db.session.query(ThemeGroup, User.id).join(
            ThemeGroup.themes,
            Theme.users_who_selected,
        ).filter(
            ThemeGroup.is_active != False,
        ).order_by(
            ThemeGroup.is_promoted.desc(),
            ThemeGroup.sort_order.asc(),
            ThemeGroup.title.asc(),
        ),

        User.id,
        get_row_key=lambda r: r[1],
        rows_to_value=lambda r_list: [r[0] for r in r_list],
    )


def get_theme_group_selected_themes_data_loader(cognito_sub):
    return get_data_loader(
        (get_theme_group_selected_themes_data_loader, cognito_sub),

        Theme.query.join(
            Theme.users_who_selected
        ).filter(
            User.cognito_sub == cognito_sub,
        ).order_by(
            Theme.sort_order.asc(),
            Theme.title.asc(),
        ),

        Theme.theme_group_id,
        get_row_key=lambda r: r.theme_group_id,
    )


def get_data_loader(
        loader_key,
        query,
        key_column,
        get_row_key=lambda r: r.id,
        rows_to_value=lambda r_list: r_list,
):
    def batch_load_fn(keys):
        rows = defaultdict(list)
        for row in query.filter(key_column.in_(keys)):
            rows[get_row_key(row)].append(row)

        return Promise.resolve([rows_to_value(rows[key]) for key in keys])

    def create_data_loader():
        return DataLoader(
            batch_load_fn=batch_load_fn,
            max_batch_size=500,
        )

    if 'm3_graphql_data_loaders' not in g:
        g.m3_graphql_data_loaders = {loader_key: create_data_loader()}

    try:
        return g.m3_graphql_data_loaders[loader_key]
    except KeyError:
        data_loader = create_data_loader()
        g.m3_graphql_data_loaders[loader_key] = data_loader
        return data_loader
