from pytest import fixture

from core.db.models import db
from core.db.models.device_token import DeviceToken


@fixture
def device_token(user):
    token = DeviceToken(
        user_id=user.id,
        token='device_token'
    )

    db.session.add(token)
    db.session.commit()

    yield token
