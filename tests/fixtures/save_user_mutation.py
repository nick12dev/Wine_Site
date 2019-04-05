import pytest
import graphene


@pytest.fixture
def save_user_mutation_query():
    return '''
mutation saveUser($input: SaveUserInput!) {
  saveUser(input: $input) {
    clientMutationId
    user {
      firstName
      email
      phone
      existsInCognito
      cognitoEnabled
      cognitoStatus
      cognitoDisplayStatus
      cognitoPhoneVerified
      cognitoEmailVerified
      userSubscription {
        state
      }
    }
  }
}'''


@pytest.fixture
def save_user_input_dict(domain_card_1, domain_card_2, domain_card_3):
    return {
        'input': {
            'clientMutationId': 'test_mutation_id',
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john.doe@test.com',
            'phone': '+123456789012',
            'avatar': 'https://test.com/someimage.png',
            'userAddress': {
                'country': 'USA',
                'stateRegion': 'California',
                'city': "San Francisco",
                'street1': 'some street 1',
                'street2': 'some street 2',
                'postcode': '79024',
            },
            'userSubscription': {
                'type': 'mixed',
                'bottleQty': 3,
                'budget': '100.00',
                'state': 'suspended',
            },
            'userCards': [
                {
                    'domainCardId': graphene.Node.to_global_id('DomainCard', domain_card_1.id),
                    'preference': 'like',
                },
                {
                    'domainCardId': graphene.Node.to_global_id('DomainCard', domain_card_2.id),
                    'preference': 'dislike',
                },
                {
                    'domainCardId': graphene.Node.to_global_id('DomainCard', domain_card_3.id),
                    'preference': 'neutral',
                },
            ],
        },
    }
