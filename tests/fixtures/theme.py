from pytest import fixture

from core.db.models import db
from core.db.models.theme import Theme


@fixture
def theme_1(theme_group_1):
    theme = Theme(
        theme_group_id=theme_group_1.id,
        title='theme 1',
        image='https://someimage.url',
        short_description='theme short desc 1',
        sort_order=1000,
        wine_types=['red'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_2(theme_group_2):
    theme = Theme(
        theme_group_id=theme_group_2.id,
        title='theme 2',
        image='https://someimage2.url',
        short_description='theme short desc 2',
        sort_order=20,
        wine_types=['red'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_3(theme_group_2):
    theme = Theme(
        theme_group_id=theme_group_2.id,
        title='theme 3',
        image='https://someimage3.url',
        short_description='theme short desc 3',
        sort_order=10,
        wine_types=['white'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_4(theme_group_3):
    theme = Theme(
        theme_group_id=theme_group_3.id,
        title='theme 4',
        image='https://someimage4.url',
        short_description='theme short desc 4',
        content_blocks=[
            {'text': 'text 1',
             'image': 'image 1'},
            {'text': 'text 2',
             'image': 'image 2'},
        ],
        sort_order=100,
        wine_types=['sparkling'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_5(theme_group_3):
    theme = Theme(
        theme_group_id=theme_group_3.id,
        title='theme 5',
        image='https://someimage5.url',
        short_description='theme short desc 5',
        sort_order=300,
        wine_types=['rose'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_6(theme_group_3):
    theme = Theme(
        theme_group_id=theme_group_3.id,
        title='theme 6',
        image='https://someimage6.url',
        short_description='theme short desc 6',
        sort_order=200,
        wine_types=['dessert'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_7(theme_group_3):
    theme = Theme(
        theme_group_id=theme_group_3.id,
        title='theme 7',
        image='https://someimage7.url',
        short_description='theme short desc 7',
        sort_order=400,
        wine_types=['sparkling', 'white'],
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_8(theme_group_4):
    theme = Theme(
        theme_group_id=theme_group_4.id,
        title='theme 8',
        image='https://someimage8.url',
        short_description='theme short desc 8',
        sort_order=2000,
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_9(theme_group_4):
    theme = Theme(
        theme_group_id=theme_group_4.id,
        title='theme 9',
        image='https://someimage9.url',
        short_description='theme short desc 9',
        sort_order=1000,
    )
    db.session.add(theme)
    db.session.commit()

    yield theme


@fixture
def theme_10(theme_group_5):
    theme = Theme(
        theme_group_id=theme_group_5.id,
        title='theme 10',
        image='https://someimage10.url',
        short_description='theme short desc 10',
        sort_order=1,
    )
    db.session.add(theme)
    db.session.commit()

    yield theme
