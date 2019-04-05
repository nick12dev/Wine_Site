from decimal import Decimal

from pytest import fixture

from core.db.models import db
from core.db.models.theme_example_wine import ThemeExampleWine


@fixture
def theme_example_wine_1(theme_4):
    example_wine = ThemeExampleWine(
        theme_id=theme_4.id,
        sort_order=22,
        name='example wine 1',
        image='https://wineimage.com/1',
        description='desc 1',
        location='location 1',
        highlights=['h1', 'h2'],
        varietals=['v1', 'v2'],
        price=Decimal('150'),
        discount_pct=Decimal('0'),
        brand='brand 1',
        product_url='https://someproduct.url/1',
        prof_reviews=[
            {'score': 85,
             'name': 'one reviewer'},
            {'score': 70,
             'name': 'another reviewer'},
        ],
    )
    db.session.add(example_wine)
    db.session.commit()

    yield example_wine


@fixture
def theme_example_wine_2(theme_4):
    example_wine = ThemeExampleWine(
        theme_id=theme_4.id,
        sort_order=11,
        name='example wine 2',
        image='https://wineimage.com/2',
        description='desc 2',
        location='location 2',
        highlights=['h1', 'h2'],
        varietals=['v1', 'v2'],
        price=Decimal('150.55'),
        discount_pct=Decimal('0.1'),
        brand='brand 2',
        product_url='https://someproduct.url/2',
    )
    db.session.add(example_wine)
    db.session.commit()

    yield example_wine
