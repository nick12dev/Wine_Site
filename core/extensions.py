# pylint: disable=invalid-name
from flask_principal import Principal

from core.db.models import db

principal = Principal(use_sessions=False)


def register_extensions(app):
    db.init_app(app)
    principal.init_app(app)
