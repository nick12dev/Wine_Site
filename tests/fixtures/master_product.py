from decimal import Decimal

from pytest import fixture

from core.db.models import db
from core.db.models.master_product import MasterProduct
from core.db.models.pipeline_review_content import PipelineReviewContent


@fixture
def master_product_1(domain_category, domain_taxonomy_node, source_1):
    master_product = MasterProduct(
        category_id=domain_category.id,
        name='master_product_1',
        source_id=source_1.id,
        brand_node_id=domain_taxonomy_node.id,
        source_identifier='source_identifier'
    )

    db.session.add(master_product)
    db.session.commit()

    yield master_product


@fixture
def product_1_review_1(pipeline_sequence_1, master_product_1, source_1, source_location):
    pipeline_review = PipelineReviewContent(
        sequence_id=pipeline_sequence_1.id,
        master_product_id=master_product_1.id,
        source_id=source_1.id,
        source_review_id=-1,
        content='review 1 1 content',
        reviewer_name='reviewer 1 1',
        review_score=Decimal('80.7'),
        source_location_id=source_location.id,
    )
    db.session.add(pipeline_review)
    db.session.commit()

    yield pipeline_review


@fixture
def product_1_review_2(pipeline_sequence_1, master_product_1, source_1, source_location):
    pipeline_review = PipelineReviewContent(
        sequence_id=pipeline_sequence_1.id,
        master_product_id=master_product_1.id,
        source_id=source_1.id,
        source_review_id=-1,
        content='review 1 2 content',
        reviewer_name='reviewer 1 2',
        review_score=Decimal('90.5'),
        source_location_id=source_location.id,
    )
    db.session.add(pipeline_review)
    db.session.commit()

    yield pipeline_review


@fixture
def product_1_review_3_zero_score(pipeline_sequence_1, master_product_1, source_1, source_location):
    pipeline_review = PipelineReviewContent(
        sequence_id=pipeline_sequence_1.id,
        master_product_id=master_product_1.id,
        source_id=source_1.id,
        source_review_id=-1,
        content='review 1 3 content',
        reviewer_name='reviewer 1 3',
        review_score=Decimal('0'),
        source_location_id=source_location.id,
    )
    db.session.add(pipeline_review)
    db.session.commit()

    yield pipeline_review


@fixture
def master_product_2(domain_category, domain_taxonomy_node, source_1):
    master_product = MasterProduct(
        category_id=domain_category.id,
        name='master_product_2',
        source_id=source_1.id,
        brand_node_id=domain_taxonomy_node.id,
        source_identifier='source_identifier'
    )

    db.session.add(master_product)
    db.session.commit()

    yield master_product


@fixture
def product_2_review_1(pipeline_sequence_1, master_product_2, source_1, source_location):
    pipeline_review = PipelineReviewContent(
        sequence_id=pipeline_sequence_1.id,
        master_product_id=master_product_2.id,
        source_id=source_1.id,
        source_review_id=-1,
        content='review 2 1 content',
        reviewer_name='reviewer 2 1',
        review_score=Decimal('78'),
        source_location_id=source_location.id,
    )
    db.session.add(pipeline_review)
    db.session.commit()

    yield pipeline_review


@fixture
def master_product_3(domain_category, domain_taxonomy_node, source_2):
    master_product = MasterProduct(
        category_id=domain_category.id,
        name='master_product_3',
        source_id=source_2.id,
        brand_node_id=domain_taxonomy_node.id,
        source_identifier='source_identifier'
    )

    db.session.add(master_product)
    db.session.commit()

    yield master_product


@fixture
def master_product_4(domain_category, domain_taxonomy_node, source_1):
    master_product = MasterProduct(
        category_id=domain_category.id,
        name='master_product_4',
        source_id=source_1.id,
        brand_node_id=domain_taxonomy_node.id,
        source_identifier='source_identifier'
    )

    db.session.add(master_product)
    db.session.commit()

    yield master_product
