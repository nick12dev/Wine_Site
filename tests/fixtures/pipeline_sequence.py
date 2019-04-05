from datetime import datetime

from pytest import fixture

from core.db.models import db
from core.db.models.pipeline_sequence import PipelineSequence


@fixture
def pipeline_sequence_1(source_1):
    source = PipelineSequence(
        source_id=source_1.id,
        state='state1',
        start_time=datetime(2018, 1, 15, 21, 30, 13, 155),
        end_time=datetime(2018, 1, 15, 21, 30, 16, 295),
        is_active=True,
        comments='comments1'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def pipeline_sequence_2(source_2):
    source = PipelineSequence(
        source_id=source_2.id,
        state='error',
        start_time=datetime(2018, 2, 15, 21, 30, 13, 155),
        end_time=datetime(2018, 2, 15, 21, 30, 16, 295),
        is_active=False,
        comments='comments2'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def pipeline_sequence_3(source_3):
    source = PipelineSequence(
        source_id=source_3.id,
        state='queued',
        start_time=datetime(2018, 1, 13, 21, 33, 13, 153),
        end_time=datetime(2018, 1, 13, 21, 33, 16, 235),
        is_active=True,
        comments='comments3'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def pipeline_sequence_4(source_4):
    source = PipelineSequence(
        source_id=source_4.id,
        state='ready',
        start_time=datetime(2018, 1, 14, 21, 30, 13, 155),
        end_time=datetime(2018, 1, 14, 21, 30, 16, 295),
        is_active=True,
        comments='comments4'
    )
    db.session.add(source)
    db.session.commit()

    yield source


@fixture
def pipeline_sequence_5(source_no_shipping):
    source = PipelineSequence(
        source_id=source_no_shipping.id,
        state='ready',
        start_time=datetime(2017, 1, 15, 21, 30, 13, 155),
        end_time=datetime(2017, 1, 15, 21, 30, 16, 295),
        is_active=False,
        comments='comments5'
    )
    db.session.add(source)
    db.session.commit()

    yield source
