from pytest import fixture

from core.db.models import db
from core.db.models.domain_taxonomy_node import DomainTaxonomyNode


@fixture
def domain_taxonomy_node(domain_attribute):
    node = DomainTaxonomyNode(
        name='name',
        attribute_id=domain_attribute.id,
        definition='definition',
        story_text=['story_text']
    )

    db.session.add(node)
    db.session.commit()

    yield node
