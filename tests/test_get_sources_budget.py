# pylint: disable=unused-argument
from core.dbmethods import get_sources_budget


def test_no_shipping_data(
        app, source_location, source_location_no_shipping, shipping_rate, salestax_rate
):

    res = get_sources_budget(
        [source_location.source_id, source_location_no_shipping.source_id], 100, 2, 123
    )

    assert res == {source_location.source_id: 82}
