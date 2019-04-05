from core.routes import core_blueprint

PREFIX = '/api/1'


def register_blueprints(app):
    app.register_blueprint(core_blueprint, url_prefix=PREFIX)
