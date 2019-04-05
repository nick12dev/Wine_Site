from pytest import fixture

from core.db.models import db
from core.db.models.domain_attribute import DomainAttribute


@fixture
def domain_attribute(domain_category):
    node = DomainAttribute(
        name='domain attribute',
        category_id=domain_category.id,
        has_taxonomy=False,
        taxonomy_is_scored=False,
        is_multivalue=False,
        is_required=False,
        is_runtime=False,
        should_extract_values=False,
        code='code',
        datatype='text',
        default_value=1,
        should_extract_from_name=False
    )

    db.session.add(node)
    db.session.commit()

    yield node
