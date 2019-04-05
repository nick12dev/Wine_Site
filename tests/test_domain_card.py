# pylint: disable=too-many-arguments


def test_get_domain_card_display_order(
        api_url,
        valid_jwt,
        client,
        domain_card_1,
        domain_card_3,
        domain_card_2
):
    query = """
      query {
        domainCards {
          edges {
            node {
              displayText
              displayOrder
              displayImage
            }
          }
        }
      }
    """  # order should be correct even if (sort: display_order_asc) is not specified explicitly

    # Test
    response = client.post(
        api_url,
        headers={
            'Authorization': 'JWT %s' % valid_jwt,
            'Content-Type': 'application/graphql',
        },
        data=query
    )

    res = [n['node']['displayText'] for n in response.json['data']['domainCards']['edges']]

    # Check
    assert res == [
        domain_card_1.display_text,
        domain_card_2.display_text,
        domain_card_3.display_text
    ]
