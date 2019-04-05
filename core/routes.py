# pylint: disable=invalid-name
import logging
from flask import (
    request,
    Blueprint,
)
from flask_graphql import GraphQLView
from core.config import (
    DEBUG,
    LOG_GQL,
)
from core.graphql import schema
from core.cognito import anonymous_user_permission

core_blueprint = Blueprint('core', __name__)

logger = logging.getLogger(__name__)


# def access_control_allow_origin(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         response = make_response(f(*args, **kwargs))
#         response.headers['Access-Control-Allow-Origin'] = '*'
#         return response
#
#     return wrapper


class LoggingGraphQLView(GraphQLView):

    def dispatch_request(self):
        try:
            logger.info('Request: %s', request.data)
        except Exception as e:
            logger.error('Can not log request.data: %s', e)

        response = super().dispatch_request()

        try:
            logger.info('Response: %s', response.response)
        except Exception as e:
            logger.error('Can not log response: %s', e)

        return response


graphql_view = LoggingGraphQLView if LOG_GQL else GraphQLView

core_blueprint.add_url_rule(
    '/',
    view_func=anonymous_user_permission.require(http_exception=401)(
        # access_control_allow_origin(
        graphql_view.as_view('graphql', schema=schema, graphiql=DEBUG)
        # )
    )
)
