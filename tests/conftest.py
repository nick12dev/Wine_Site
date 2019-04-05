# pylint: disable=redefined-outer-name,invalid-name,no-member
#         (pytest fixtures would not work otherwise)
import os
import copy
from pathlib import Path

import pytest

from core.startup import create_app
from core.db.models import db

pytest_plugins = [
    'tests.fixtures.authorization',
    'tests.fixtures.api',
    'tests.fixtures.domain_card',
    'tests.fixtures.user',
    'tests.fixtures.theme_group',
    'tests.fixtures.theme',
    'tests.fixtures.theme_example_wine',
    'tests.fixtures.user_subscription',
    'tests.fixtures.order',
    'tests.fixtures.order_shipping_carrier',
    'tests.fixtures.order_shipping_method',
    'tests.fixtures.save_user_mutation',
    'tests.fixtures.user_address',
    'tests.fixtures.device_token',
    'tests.fixtures.master_product',
    'tests.fixtures.domain_attribute',
    'tests.fixtures.domain_taxonomy_node',
    'tests.fixtures.source',
    'tests.fixtures.user_card',
    'tests.fixtures.pipeline_sequence',
    'tests.fixtures.product_offer',
    'tests.fixtures.offer_item',
    'tests.fixtures.graphql_client',
    'tests.fixtures.source_location',
    'tests.fixtures.salestax_rate',
    'tests.fixtures.shipping_rate',
]


@pytest.fixture
def test_data_folder():
    return Path(__file__).parents[0] / 'data'


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr('requests.sessions.Session.request')


@pytest.fixture
def app(monkeypatch, sample_jwks):
    jwks = copy.deepcopy(sample_jwks)
    for key in jwks['keys']:
        del key['d']  # remove private part of the key

    def mock_download_jwks():
        return jwks

    def mock_load_domain_category_id():
        pass

    monkeypatch.setattr('core.cognito.download_jwks', mock_download_jwks)
    monkeypatch.setattr('core.startup._load_domain_category_id', mock_load_domain_category_id)

    app = create_app()
    app.app_context().push()

    assert os.environ['SQLALCHEMY_DATABASE_URI'].endswith('m3_test')
    db.session.rollback()  # kill hanging "in-progress" transaction if any (happens when previous tests fail)
    db.engine.execute(
        '''
        delete from themes_example_wines;
        delete from user_themes;
        delete from user_creators;
        delete from device_tokens;
        delete from domain_attributes;
        delete from user_cards;
        delete from offer_items;
        delete from themes;
        delete from theme_groups;
        delete from domain_cards;
        delete from pipeline_review_content;
        delete from master_products;
        delete from domain_categories;
        delete from domain_taxonomy_nodes;
        delete from order_history;
        delete from pipeline_sequence;
        delete from product_offers;
        delete from user_subscription_snapshots;
        delete from orders;
        delete from order_shipping_methods;
        delete from order_shipping_carriers;
        delete from shipping_rates;
        delete from salestax_rates;
        delete from sources;
        update users set primary_user_address_id=null, primary_user_subscription_id=null;
        delete from user_addresses;
        delete from user_subscriptions;
        delete from users;
        '''
    )

    yield app

    db.session.close()
    db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
