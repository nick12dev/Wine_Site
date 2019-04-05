from pytest import fixture

from core.db.models import db
from core.db.models.source import Source


@fixture
def source_1():
    source = Source(
        name='source_1',
        source_url='source_url'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def source_2():
    source = Source(
        name='source_2',
        source_url='source_url_2'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def source_3():
    source = Source(
        name='source_3',
        source_url='source_url_3'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def source_4():
    source = Source(
        name='source_source_4',
        source_url='source_url_4'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def source_no_shipping():
    source = Source(
        name='source_no_shipping',
        source_url='source_url_no_shipping'
    )
    db.session.add(source)
    db.session.commit()

    yield source
