import pytest


@pytest.fixture
def api_url():
    return '/api/1/'


@pytest.fixture
def domain_cards_query():
    return '''
{
  domainCards {
    edges {
      node {
        id,
        displayText,
        displayTitle,
        displayImage,
        displayOrder,
      }
    }
  }
}'''


@pytest.fixture
def user_query():
    return '''
{
  user {
    firstName
    lastName
    email
    phone
    avatar
    registrationFinished
    userAddress {
      country
      stateRegion
      city
      street1
      street2
      postcode
    }
    userSubscription {
      type
      bottleQty
      budget
    }
    userCards {
      edges {
        node {
          domainCardId
          preference
        }
      }
    }
  }
}'''
