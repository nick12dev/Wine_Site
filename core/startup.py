# pylint: disable=wrong-import-position,unused-variable
import gevent.monkey

gevent.monkey.patch_all()

#from psycogreen.gevent import patch_psycopg

#patch_psycopg()

import logging

from flask import (
    Flask,
    current_app,
    request,
    redirect,
    url_for,
    Response,
)
from core.cognito import (
    populate_jwk_dict,
    exchange_auth_code_for_jwts,
)
from core.extensions import register_extensions
from core.blueprints import register_blueprints
from core.db.models.domain_category import DomainCategory
# from core.config import SUBSCRIPTIONS_DEEPLINK

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    register_extensions(app)
    register_blueprints(app)

    @app.before_first_request
    def startup_routine():
        populate_jwk_dict()
        _load_domain_category_id()

    @app.route('/health')
    def healthcheck():
        return Response(status=200)


    #@app.route('/deeplink/subscriptions/')
    #def deeplink():
    #    location = SUBSCRIPTIONS_DEEPLINK
    #
    #    subscription_id = request.args.get('id')
    #    if subscription_id:
    #        location += '/%s' % subscription_id
    #
    #    return redirect(location)

    # @app.errorhandler(401)
    # def unauthorized(e):
    #     return 'Unauthorized', 401

    if app.debug:
        # The following helps checking Cognito integration without the client app
        # (not needed otherwise).

        @app.route('/')
        def force_login():
            try:
                cognito_auth_code = request.args['code']
            except KeyError:
                return redirect(current_app.config['COGNITO_LOGIN_PAGE_URL'])

            response = redirect(url_for('core.graphql'))
            response.set_cookie(
                'cognito_access_token',
                exchange_auth_code_for_jwts(cognito_auth_code)['access_token']
            )
            return response

    return app


def _load_domain_category_id():
    a=5
    print("------------")
    print("------------")
    
    # current_app.config['M3_DOMAIN_CATEGORY_ID'] = DomainCategory.query.filter_by(
    #     name=current_app.config['M3_DOMAIN_CATEGORY_NAME']
    # ).first().id
