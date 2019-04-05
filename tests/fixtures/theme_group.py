from core.db.models.theme_group import ThemeGroup
from pytest import fixture

from core.db.models import db
from core.dbmethods.user import populate_automatic_username


@fixture
def theme_group_1(user):
    theme_group = ThemeGroup(
        user_id=user.id,
        sort_order=10,
        is_active=False,
        is_promoted=False,
        title='theme group 1',
        description='theme group desc 1',
    )
    db.session.add(theme_group)
    user.is_creator = True
    db.session.commit()
    populate_automatic_username(user)

    yield theme_group


@fixture
def theme_group_2(user2):
    theme_group = ThemeGroup(
        user_id=user2.id,
        sort_order=30,
        is_active=True,
        is_promoted=False,
        title='theme group 2',
        description='theme group desc 2',
    )
    db.session.add(theme_group)
    user2.is_creator = True
    db.session.commit()
    populate_automatic_username(user2)

    yield theme_group


@fixture
def theme_group_3(user4):
    theme_group = ThemeGroup(
        user_id=user4.id,
        sort_order=40,
        is_active=True,
        is_promoted=True,
        title='theme group 3',
        description='theme group desc 3',
    )
    db.session.add(theme_group)
    user4.is_creator = True
    db.session.commit()
    populate_automatic_username(user4)

    yield theme_group


@fixture
def theme_group_4(user4):
    theme_group = ThemeGroup(
        user_id=user4.id,
        sort_order=20,
        is_active=True,
        is_promoted=False,
        title='theme group 4',
        description='theme group desc 4',
    )
    db.session.add(theme_group)
    user4.is_creator = True
    db.session.commit()
    populate_automatic_username(user4)

    yield theme_group


@fixture
def theme_group_5(user4):
    theme_group = ThemeGroup(
        user_id=user4.id,
        sort_order=5,
        is_active=False,
        is_promoted=True,
        title='theme group 5',
        description='theme group desc 5',
    )
    db.session.add(theme_group)
    user4.is_creator = True
    db.session.commit()
    populate_automatic_username(user4)

    yield theme_group


@fixture
def empty_theme_group(user4):
    theme_group = ThemeGroup(
        user_id=user4.id,
        sort_order=3,
        is_active=True,
        is_promoted=True,
        title='empty theme group',
        description='empty theme group desc',
    )
    db.session.add(theme_group)
    user4.is_creator = True
    db.session.commit()
    populate_automatic_username(user4)

    yield theme_group
