# pylint: disable=unused-argument,bad-continuation,line-too-long
from datetime import datetime
from unittest.mock import patch

from graphene import Node

from core.db.models import db
from core.db.models.user import User
from core.dbmethods.user import populate_automatic_username
from core.graphql.schemas import (
    SORT_SELECTED_THEMES_SELECTED_AT_ASC,
    SORT_SELECTED_THEMES_SELECTED_AT_DESC,
)


def test_theme_list(
        graphql_client_anonymous,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
        theme_example_wine_1,
        theme_example_wine_2,
):
    query = '''
      query {
        themes {
          edges {
            node {
              title
              image
              shortDescription
              sortOrder
              isSelected
              themeGroup {
                title
                description
                isActive
                isPromoted
                sortOrder
                user {
                  firstName
                  lastName
                  avatar
                  followerCount
                }
              }
              contentBlocks {
                image
                text
              }
              exampleWines {
                edges {
                  node {
                    sortOrder
                    name
                    image
                    description
                    location
                    highlights
                    varietals
                    price
                    brand
                    productUrl}}}}}}}
    '''

    res = graphql_client_anonymous.post(query)
    expected = {'data': {'themes': {'edges': [
        {'node': {'exampleWines': {'edges': [{'node': {'brand': 'brand 2',
                                                       'description': 'desc 2',
                                                       'highlights': ['h1', 'h2'],
                                                       'image': 'https://wineimage.com/2',
                                                       'location': 'location 2',
                                                       'name': 'example wine 2',
                                                       'price': '150.55',
                                                       'productUrl': 'https://someproduct.url/2',
                                                       'sortOrder': 11,
                                                       'varietals': ['v1', 'v2']}},
                                             {'node': {'brand': 'brand 1',
                                                       'description': 'desc 1',
                                                       'highlights': ['h1', 'h2'],
                                                       'image': 'https://wineimage.com/1',
                                                       'location': 'location 1',
                                                       'name': 'example wine 1',
                                                       'price': '150',
                                                       'productUrl': 'https://someproduct.url/1',
                                                       'sortOrder': 22,
                                                       'varietals': ['v1', 'v2']}}]},
                  'contentBlocks': [{'image': 'image 1',
                                     'text': 'text 1'},
                                    {'image': 'image 2',
                                     'text': 'text 2'}],
                  'image': 'https://someimage4.url',
                  'shortDescription': 'theme short desc 4',
                  'sortOrder': 100,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 3',
                                 'isActive': True,
                                 'isPromoted': True,
                                 'sortOrder': 40,
                                 'title': 'theme group 3',
                                 'user': {'avatar': 'https://some.pic/url/4/',
                                          'followerCount': 0,
                                          'firstName': 'tuser4',
                                          'lastName': 'tlastname4'}},
                  'title': 'theme 4'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage6.url',
                  'shortDescription': 'theme short desc 6',
                  'sortOrder': 200,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 3',
                                 'isActive': True,
                                 'isPromoted': True,
                                 'sortOrder': 40,
                                 'title': 'theme group 3',
                                 'user': {'avatar': 'https://some.pic/url/4/',
                                          'followerCount': 0,
                                          'firstName': 'tuser4',
                                          'lastName': 'tlastname4'}},
                  'title': 'theme 6'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage5.url',
                  'shortDescription': 'theme short desc 5',
                  'sortOrder': 300,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 3',
                                 'isActive': True,
                                 'isPromoted': True,
                                 'sortOrder': 40,
                                 'title': 'theme group 3',
                                 'user': {'avatar': 'https://some.pic/url/4/',
                                          'followerCount': 0,
                                          'firstName': 'tuser4',
                                          'lastName': 'tlastname4'}},
                  'title': 'theme 5'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage7.url',
                  'shortDescription': 'theme short desc 7',
                  'sortOrder': 400,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 3',
                                 'isActive': True,
                                 'isPromoted': True,
                                 'sortOrder': 40,
                                 'title': 'theme group 3',
                                 'user': {'avatar': 'https://some.pic/url/4/',
                                          'followerCount': 0,
                                          'firstName': 'tuser4',
                                          'lastName': 'tlastname4'}},
                  'title': 'theme 7'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage9.url',
                  'shortDescription': 'theme short desc 9',
                  'sortOrder': 1000,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 4',
                                 'isActive': True,
                                 'isPromoted': False,
                                 'sortOrder': 20,
                                 'title': 'theme group 4',
                                 'user': {'avatar': 'https://some.pic/url/4/',
                                          'followerCount': 0,
                                          'firstName': 'tuser4',
                                          'lastName': 'tlastname4'}},
                  'title': 'theme 9'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage8.url',
                  'shortDescription': 'theme short desc 8',
                  'sortOrder': 2000,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 4',
                                 'isActive': True,
                                 'isPromoted': False,
                                 'sortOrder': 20,
                                 'title': 'theme group 4',
                                 'user': {'avatar': 'https://some.pic/url/4/',
                                          'followerCount': 0,
                                          'firstName': 'tuser4',
                                          'lastName': 'tlastname4'}},
                  'title': 'theme 8'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage3.url',
                  'shortDescription': 'theme short desc 3',
                  'sortOrder': 10,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 2',
                                 'isActive': True,
                                 'isPromoted': False,
                                 'sortOrder': 30,
                                 'title': 'theme group 2',
                                 'user': {'avatar': None,
                                          'followerCount': 0,
                                          'firstName': 'tuser2',
                                          'lastName': None}},
                  'title': 'theme 3'}},
        {'node': {'exampleWines': {'edges': []},
                  'contentBlocks': [],
                  'image': 'https://someimage2.url',
                  'shortDescription': 'theme short desc 2',
                  'sortOrder': 20,
                  'isSelected': False,
                  'themeGroup': {'description': 'theme group desc 2',
                                 'isActive': True,
                                 'isPromoted': False,
                                 'sortOrder': 30,
                                 'title': 'theme group 2',
                                 'user': {'avatar': None,
                                          'followerCount': 0,
                                          'firstName': 'tuser2',
                                          'lastName': None}},
                  'title': 'theme 2'}}]}}}
    assert res == expected


def test_theme_group_list(
        graphql_client,
        graphql_client_anonymous,
        user2,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        theme_group_1,
        theme_group_2,
        theme_group_3,
        theme_group_4,
        theme_group_5,
        empty_theme_group,
        theme_example_wine_1,
        theme_example_wine_2,
):
    query = '''
      query AllThemeGroups {
        themeGroups {
          __typename
          edges {
            __typename
            node {
              __typename
              id
              sortOrder
              isPromoted
              title
              description
              isActive
              user {
                __typename
                id
                firstName
                isCreator
                avatar
                phone
                email
                followerCount
                bio
                lastName
              }
              themes {
                __typename
                edges {
                  __typename
                  node {
                    __typename
                    id
                    title
                    image
                    shortDescription
                    sortOrder
                    isSelected
                    wineTypes
                    isRedTheme
                    isWhiteTheme
                    contentBlocks {
                      __typename
                      image
                      text
                    }
                    exampleWines {
                      __typename
                      edges {
                        __typename
                        node {
                          __typename
                          id
                          name
                          scoreNum
                          image
                          description
                          sortOrder
                          location
                          highlights
                          varietals
                          qty
                          brand
                          productUrl
                          price
                          msrp
                          productReviews {
                            __typename
                            reviewerName
                            reviewScore
                          }
                          topProductReview {
                            __typename
                            reviewerName
                            reviewScore}}}}}}}}}}}
    '''

    expected = {'data': {'themeGroups': {'__typename': 'ThemeGroupsConnection', 'edges': [
        {'__typename': 'ThemeGroupsEdge',
         'node': {'__typename': 'ThemeGroup',
                  'id': Node.to_global_id('ThemeGroup', theme_group_3.id),
                  'description': 'theme group desc 3',
                  'isActive': True,
                  'isPromoted': True,
                  'sortOrder': 40,
                  'themes': {
                      '__typename': 'ThemeConnection',
                      'edges': [{'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_4.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': [{'__typename': 'ThemesExampleWinesEdge',
                                                                      'node': {'__typename': 'ThemeExampleWine',
                                                                               'id': Node.to_global_id(
                                                                                   'ThemeExampleWine',
                                                                                   theme_example_wine_2.id
                                                                               ),
                                                                               'brand': 'brand 2',
                                                                               'description': 'desc 2',
                                                                               'highlights': ['h1', 'h2'],
                                                                               'image': 'https://wineimage.com/2',
                                                                               'location': 'location 2',
                                                                               'name': 'example wine 2',
                                                                               'price': '150.55',
                                                                               'msrp': None,
                                                                               'qty': None,
                                                                               'scoreNum': None,
                                                                               'productReviews': [],
                                                                               'topProductReview': None,
                                                                               'productUrl': 'https://someproduct.url/2',
                                                                               'sortOrder': 11,
                                                                               'varietals': ['v1', 'v2']}},
                                                                     {'__typename': 'ThemesExampleWinesEdge',
                                                                      'node': {'__typename': 'ThemeExampleWine',
                                                                               'id': Node.to_global_id(
                                                                                   'ThemeExampleWine',
                                                                                   theme_example_wine_1.id
                                                                               ),
                                                                               'brand': 'brand 1',
                                                                               'description': 'desc 1',
                                                                               'highlights': ['h1', 'h2'],
                                                                               'image': 'https://wineimage.com/1',
                                                                               'location': 'location 1',
                                                                               'name': 'example wine 1',
                                                                               'price': '150',
                                                                               'msrp': None,
                                                                               'qty': None,
                                                                               'scoreNum': None,
                                                                               'productReviews': [
                                                                                   {'__typename': 'ProductReview',
                                                                                    'reviewScore': 85,
                                                                                    'reviewerName': 'one '
                                                                                                    'reviewer'},
                                                                                   {'__typename': 'ProductReview',
                                                                                    'reviewScore': 70,
                                                                                    'reviewerName': 'another '
                                                                                                    'reviewer'}],
                                                                               'topProductReview': {
                                                                                   '__typename': 'ProductReview',
                                                                                   'reviewScore': 85,
                                                                                   'reviewerName': 'one '
                                                                                                   'reviewer'},
                                                                               'productUrl': 'https://someproduct.url/1',
                                                                               'sortOrder': 22,
                                                                               'varietals': ['v1', 'v2']}}]},
                                          'contentBlocks': [{'__typename': 'ContentBlock',
                                                             'image': 'image 1',
                                                             'text': 'text 1'},
                                                            {'__typename': 'ContentBlock',
                                                             'image': 'image 2',
                                                             'text': 'text 2'}],
                                          'image': 'https://someimage4.url',
                                          'shortDescription': 'theme short desc 4',
                                          'sortOrder': 100,
                                          'isSelected': False,
                                          'wineTypes': ['sparkling'],
                                          'isRedTheme': False,
                                          'isWhiteTheme': False,
                                          'title': 'theme 4'}},
                                {'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_6.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage6.url',
                                          'shortDescription': 'theme short desc 6',
                                          'sortOrder': 200,
                                          'isSelected': False,
                                          'wineTypes': ['dessert'],
                                          'isRedTheme': False,
                                          'isWhiteTheme': False,
                                          'title': 'theme 6'}},
                                {'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_5.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage5.url',
                                          'shortDescription': 'theme short desc 5',
                                          'sortOrder': 300,
                                          'isSelected': False,
                                          'wineTypes': ['rose'],
                                          'isRedTheme': False,
                                          'isWhiteTheme': False,
                                          'title': 'theme 5'}},
                                {'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_7.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage7.url',
                                          'shortDescription': 'theme short desc 7',
                                          'sortOrder': 400,
                                          'isSelected': False,
                                          'wineTypes': ['sparkling', 'white'],
                                          'isRedTheme': False,
                                          'isWhiteTheme': True,
                                          'title': 'theme 7'}}]},
                  'title': 'theme group 3',
                  'user': {'__typename': 'User',
                           'id': Node.to_global_id('User', user4.id),
                           'avatar': 'https://some.pic/url/4/',
                           'followerCount': 0,
                           'bio': 'test bio 4',
                           'isCreator': True,
                           'email': None,
                           'phone': None,
                           'firstName': 'tuser4',
                           'lastName': 'tlastname4'}}},
        {'__typename': 'ThemeGroupsEdge',
         'node': {'__typename': 'ThemeGroup',
                  'id': Node.to_global_id('ThemeGroup', theme_group_4.id),
                  'description': 'theme group desc 4',
                  'isActive': True,
                  'isPromoted': False,
                  'sortOrder': 20,
                  'themes': {
                      '__typename': 'ThemeConnection',
                      'edges': [{'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_9.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage9.url',
                                          'shortDescription': 'theme short desc 9',
                                          'sortOrder': 1000,
                                          'isSelected': False,
                                          'wineTypes': [],
                                          'isRedTheme': False,
                                          'isWhiteTheme': False,
                                          'title': 'theme 9'}},
                                {'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_8.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage8.url',
                                          'shortDescription': 'theme short desc 8',
                                          'sortOrder': 2000,
                                          'isSelected': False,
                                          'wineTypes': [],
                                          'isRedTheme': False,
                                          'isWhiteTheme': False,
                                          'title': 'theme 8'}}]},
                  'title': 'theme group 4',
                  'user': {'__typename': 'User',
                           'id': Node.to_global_id('User', user4.id),
                           'avatar': 'https://some.pic/url/4/',
                           'followerCount': 0,
                           'bio': 'test bio 4',
                           'isCreator': True,
                           'email': None,
                           'phone': None,
                           'firstName': 'tuser4',
                           'lastName': 'tlastname4'}}},
        {'__typename': 'ThemeGroupsEdge',
         'node': {'__typename': 'ThemeGroup',
                  'id': Node.to_global_id('ThemeGroup', theme_group_2.id),
                  'description': 'theme group desc 2',
                  'isActive': True,
                  'isPromoted': False,
                  'sortOrder': 30,
                  'themes': {
                      '__typename': 'ThemeConnection',
                      'edges': [{'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_3.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage3.url',
                                          'shortDescription': 'theme short desc 3',
                                          'sortOrder': 10,
                                          'isSelected': False,
                                          'wineTypes': ['white'],
                                          'isRedTheme': False,
                                          'isWhiteTheme': True,
                                          'title': 'theme 3'}},
                                {'__typename': 'ThemeEdge',
                                 'node': {'__typename': 'Theme',
                                          'id': Node.to_global_id('Theme', theme_2.id),
                                          'exampleWines': {'__typename': 'ThemesExampleWinesConnection',
                                                           'edges': []},
                                          'contentBlocks': [],
                                          'image': 'https://someimage2.url',
                                          'shortDescription': 'theme short desc 2',
                                          'sortOrder': 20,
                                          'isSelected': False,
                                          'wineTypes': ['red'],
                                          'isRedTheme': True,
                                          'isWhiteTheme': False,
                                          'title': 'theme 2'}}]},
                  'title': 'theme group 2',
                  'user': {'__typename': 'User',
                           'id': Node.to_global_id('User', user2.id),
                           'avatar': None,
                           'followerCount': 0,
                           'bio': None,
                           'isCreator': True,
                           'email': None,
                           'phone': None,
                           'firstName': 'tuser2',
                           'lastName': None}}}]}}}

    res = graphql_client.post(query)
    assert res == expected

    res = graphql_client_anonymous.post(query)
    assert res == expected


set_user_theme_selections_query = '''
  mutation($input: SetUserThemeSelectionsInput!) {
    setUserThemeSelections(input: $input) {
      clientMutationId}}
'''


def _set_user_theme_selections(graphql_client, selections):
    res = graphql_client.post(set_user_theme_selections_query, variables={
        'input': {
            'themeSelections': [
                {
                    'themeId': Node.to_global_id('Theme', selection[0]),
                    'selected': selection[1],
                } for selection in selections
            ],
        },
    })
    expected = {'data': {'setUserThemeSelections': {'clientMutationId': None}}}
    return res, expected


def test_user_select_theme_follow_creator(
        graphql_client,
        wine_expert,
        user,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
        theme_example_wine_1,
        theme_example_wine_2,
):
    user_id = user.id
    user4_id = user4.id
    theme_4_id = theme_4.id
    theme_6_id = theme_6.id

    assert user.selected_themes == []
    assert user.followed_creators == []

    res, expected = _set_user_theme_selections(graphql_client, [(theme_4_id, True)])
    assert res == expected

    user = User.query.filter(User.id == user_id).first()
    assert len(user.selected_themes) == 1
    assert user.selected_themes[0].id == theme_4_id
    assert len(user.followed_creators) == 1
    assert user.followed_creators[0].id == user4_id

    res, expected = _set_user_theme_selections(graphql_client, [(theme_6_id, True)])
    assert res == expected

    user = User.query.filter(User.id == user_id).first()
    assert len(user.selected_themes) == 2
    assert {st.id for st in user.selected_themes} == {theme_4_id, theme_6_id}
    assert len(user.followed_creators) == 1
    assert user.followed_creators[0].id == user4_id

    res, expected = _set_user_theme_selections(graphql_client, [(theme_6_id, False)])
    assert res == expected

    user = User.query.filter(User.id == user_id).first()
    assert len(user.selected_themes) == 1
    assert user.selected_themes[0].id == theme_4_id
    assert len(user.followed_creators) == 1
    assert user.followed_creators[0].id == user4_id

    res, expected = _set_user_theme_selections(graphql_client, [(theme_4_id, False)])
    assert res == expected

    user = User.query.filter(User.id == user_id).first()
    assert user.selected_themes == []
    assert user.followed_creators == []


def test_user_red_white_themes_selected(
        app,
        graphql_client,
        graphql_client_admin,
        user_subscription,
        user_subscription2,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
):
    theme_1_id = theme_1.id
    theme_2_id = theme_2.id
    theme_3_id = theme_3.id
    theme_4_id = theme_4.id
    theme_5_id = theme_5.id
    theme_6_id = theme_6.id
    theme_7_id = theme_7.id
    theme_8_id = theme_8.id
    theme_9_id = theme_9.id
    theme_10_id = theme_10.id

    query = '''
      {
        user {
          userSubscription {
            redThemesSelected
            whiteThemesSelected}}}
    '''

    res, expected = _set_user_theme_selections(graphql_client_admin, [
        (theme_2_id, True),  # red theme - wrong user
    ])
    assert res == expected
    with app.app_context():
        res = graphql_client.post(query)
    expected = {'data': {'user': {'userSubscription': {
        'redThemesSelected': False,
        'whiteThemesSelected': False
    }}}}
    assert res == expected

    res, expected = _set_user_theme_selections(graphql_client, [
        (theme_1_id, True),  # red theme - inactive theme group
        (theme_4_id, True),  # sparkling theme
        (theme_5_id, True),  # rose theme
        (theme_6_id, True),  # dessert theme
        (theme_8_id, True),  # theme without wine type
        (theme_9_id, True),  # theme without wine type
        (theme_10_id, True),  # theme without wine type
    ])
    assert res == expected
    with app.app_context():
        res = graphql_client.post(query)
    expected = {'data': {'user': {'userSubscription': {
        'redThemesSelected': False,
        'whiteThemesSelected': False,
    }}}}
    assert res == expected

    res, expected = _set_user_theme_selections(graphql_client, [
        (theme_2_id, True),  # red theme
    ])
    assert res == expected
    with app.app_context():
        res = graphql_client.post(query)
    expected = {'data': {'user': {'userSubscription': {
        'redThemesSelected': True,
        'whiteThemesSelected': False,
    }}}}
    assert res == expected

    res, expected = _set_user_theme_selections(graphql_client, [
        (theme_7_id, True),  # sparkling/white theme
    ])
    assert res == expected
    with app.app_context():
        res = graphql_client.post(query)
    expected = {'data': {'user': {'userSubscription': {
        'redThemesSelected': True,
        'whiteThemesSelected': True,
    }}}}
    assert res == expected

    res, expected = _set_user_theme_selections(graphql_client, [
        (theme_3_id, True),  # white theme
    ])
    assert res == expected
    with app.app_context():
        res = graphql_client.post(query)
    expected = {'data': {'user': {'userSubscription': {
        'redThemesSelected': True,
        'whiteThemesSelected': True,
    }}}}
    assert res == expected


def test_user_selected_theme_groups_and_followed_creators(
        graphql_client,
        graphql_client_admin,
        user,
        user2,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
):
    theme_1_id = theme_1.id
    theme_2_id = theme_2.id
    theme_5_id = theme_5.id
    theme_6_id = theme_6.id
    theme_7_id = theme_7.id
    theme_9_id = theme_9.id

    res, expected = _set_user_theme_selections(graphql_client, [
        (theme_1_id, True),
        (theme_2_id, True),
        (theme_5_id, True),
        (theme_6_id, True),
        (theme_9_id, True),
    ])
    assert res == expected
    res, expected = _set_user_theme_selections(graphql_client_admin, [
        (theme_7_id, True),
    ])
    assert res == expected

    query = '''
      {
        user {
          followedCreators {
            edges {
              node {
                firstName
                lastName
                avatar
                isCreator
                bio
                followerCount
              }
            }
          }
          selectedThemeGroups {
            edges {
              node {
                title
                description
                isActive
                isPromoted
                sortOrder
                user {
                  firstName
                  lastName
                  avatar
                  isCreator
                  bio
                  followerCount
                }
                selectedThemes {
                  title
                  image
                  shortDescription
                  sortOrder
                  isSelected
                  contentBlocks {
                    image
                    text
                  }
                  exampleWines {
                    edges {
                      node {
                        sortOrder
                        name
                        image
                        description
                        location
                        highlights
                        varietals
                        price
                        brand
                        productUrl}}}}}}}}}
    '''

    res = graphql_client.post(query)

    expected = {'data': {'user': {'followedCreators': {'edges': [
        {'node': {'avatar': None,
                  'bio': None,
                  'followerCount': 1,
                  'firstName': 'tuser',
                  'isCreator': True,
                  'lastName': None}},
        {'node': {'avatar': None,
                  'bio': None,
                  'followerCount': 1,
                  'firstName': 'tuser2',
                  'isCreator': True,
                  'lastName': None}},
        {'node': {'avatar': 'https://some.pic/url/4/',
                  'bio': 'test bio 4',
                  'followerCount': 2,
                  'firstName': 'tuser4',
                  'isCreator': True,
                  'lastName': 'tlastname4'}}]},
        'selectedThemeGroups': {'edges': [
            {'node': {'description': 'theme group desc 3',
                      'isActive': True,
                      'isPromoted': True,
                      'selectedThemes': [{'contentBlocks': [],
                                          'exampleWines': {'edges': []},
                                          'image': 'https://someimage6.url',
                                          'shortDescription': 'theme short desc 6',
                                          'sortOrder': 200,
                                          'isSelected': True,
                                          'title': 'theme 6'},
                                         {'contentBlocks': [],
                                          'exampleWines': {'edges': []},
                                          'image': 'https://someimage5.url',
                                          'shortDescription': 'theme short desc 5',
                                          'sortOrder': 300,
                                          'isSelected': True,
                                          'title': 'theme 5'}],
                      'sortOrder': 40,
                      'title': 'theme group 3',
                      'user': {'avatar': 'https://some.pic/url/4/',
                               'bio': 'test bio 4',
                               'followerCount': 2,
                               'firstName': 'tuser4',
                               'isCreator': True,
                               'lastName': 'tlastname4'}}},
            {'node': {'description': 'theme group desc 4',
                      'isActive': True,
                      'isPromoted': False,
                      'selectedThemes': [{'contentBlocks': [],
                                          'exampleWines': {'edges': []},
                                          'image': 'https://someimage9.url',
                                          'isSelected': True,
                                          'shortDescription': 'theme short desc 9',
                                          'sortOrder': 1000,
                                          'title': 'theme 9'}],
                      'sortOrder': 20,
                      'title': 'theme group 4',
                      'user': {'avatar': 'https://some.pic/url/4/',
                               'bio': 'test bio 4',
                               'firstName': 'tuser4',
                               'followerCount': 2,
                               'isCreator': True,
                               'lastName': 'tlastname4'}}},
            {'node': {'description': 'theme group desc 2',
                      'isActive': True,
                      'isPromoted': False,
                      'selectedThemes': [{'contentBlocks': [],
                                          'exampleWines': {'edges': []},
                                          'image': 'https://someimage2.url',
                                          'shortDescription': 'theme short desc 2',
                                          'sortOrder': 20,
                                          'isSelected': True,
                                          'title': 'theme 2'}],
                      'sortOrder': 30,
                      'title': 'theme group 2',
                      'user': {'avatar': None,
                               'bio': None,
                               'followerCount': 1,
                               'firstName': 'tuser2',
                               'isCreator': True,
                               'lastName': None}}}]}}}}

    assert res == expected


creator_profile_query = '''
  query($userId: ID!) {
    creator: node(id: $userId) {
      ... on User {
        firstName
        lastName
        username
        avatar
        isCreator
        bio
        followerCount
        themeGroups {
          edges {
            node {
              title
              description
              isActive
              isPromoted
              sortOrder
              themes {
                edges {
                  node {
                    title
                    image
                    shortDescription
                    sortOrder
                    isSelected
                    contentBlocks {
                      image
                      text
                    }
                    exampleWines {
                      edges {
                        node {
                          sortOrder
                          name
                          image
                          description
                          location
                          highlights
                          varietals
                          price
                          brand
                          productUrl}}}}}}}}}}}}
'''


def test_get_creator_profile(
        graphql_client_anonymous,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
        theme_example_wine_1,
        theme_example_wine_2,
):
    res = graphql_client_anonymous.post(creator_profile_query, variables={
        'userId': Node.to_global_id('User', user4.id)
    })

    expected = {'data': {'creator': {
        'avatar': 'https://some.pic/url/4/',
        'bio': 'test bio 4',
        'firstName': 'tuser4',
        'lastName': 'tlastname4',
        'username': 'tuser4.tlastname4',
        'followerCount': 0,
        'isCreator': True,
        'themeGroups': {'edges': [
            {'node': {'description': 'theme group desc 3',
                      'isActive': True,
                      'isPromoted': True,
                      'sortOrder': 40,
                      'themes': {'edges': [
                          {'node': {
                              'contentBlocks': [{'image': 'image 1',
                                                 'text': 'text 1'},
                                                {'image': 'image 2',
                                                 'text': 'text 2'}],
                              'exampleWines': {'edges': [
                                  {'node': {'brand': 'brand 2',
                                            'description': 'desc 2',
                                            'highlights': ['h1', 'h2'],
                                            'image': 'https://wineimage.com/2',
                                            'location': 'location 2',
                                            'name': 'example wine 2',
                                            'price': '150.55',
                                            'productUrl': 'https://someproduct.url/2',
                                            'sortOrder': 11,
                                            'varietals': ['v1', 'v2']}},
                                  {'node': {'brand': 'brand 1',
                                            'description': 'desc 1',
                                            'highlights': ['h1', 'h2'],
                                            'image': 'https://wineimage.com/1',
                                            'location': 'location 1',
                                            'name': 'example wine 1',
                                            'price': '150',
                                            'productUrl': 'https://someproduct.url/1',
                                            'sortOrder': 22,
                                            'varietals': ['v1', 'v2']}}]},
                              'image': 'https://someimage4.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 4',
                              'sortOrder': 100,
                              'title': 'theme 4'}},
                          {'node': {
                              'contentBlocks': [],
                              'exampleWines': {'edges': []},
                              'image': 'https://someimage6.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 6',
                              'sortOrder': 200,
                              'title': 'theme 6'}},
                          {'node': {
                              'contentBlocks': [],
                              'exampleWines': {'edges': []},
                              'image': 'https://someimage5.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 5',
                              'sortOrder': 300,
                              'title': 'theme 5'}},
                          {'node': {
                              'contentBlocks': [],
                              'exampleWines': {'edges': []},
                              'image': 'https://someimage7.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 7',
                              'sortOrder': 400,
                              'title': 'theme 7'}}]},
                      'title': 'theme group 3'}},
            {'node': {'description': 'theme group desc 4',
                      'isActive': True,
                      'isPromoted': False,
                      'sortOrder': 20,
                      'themes': {'edges': [
                          {'node': {'contentBlocks': [],
                                    'exampleWines': {'edges': []},
                                    'image': 'https://someimage9.url',
                                    'isSelected': False,
                                    'shortDescription': 'theme short desc 9',
                                    'sortOrder': 1000,
                                    'title': 'theme 9'}},
                          {'node': {'contentBlocks': [],
                                    'exampleWines': {'edges': []},
                                    'image': 'https://someimage8.url',
                                    'isSelected': False,
                                    'shortDescription': 'theme short desc 8',
                                    'sortOrder': 2000,
                                    'title': 'theme 8'}}]},
                      'title': 'theme group 4'}}]}}}}

    assert res == expected


def test_get_noncreator_profile_registered(
        graphql_client,
        user4,
):
    res = graphql_client.post(creator_profile_query, variables={
        'userId': Node.to_global_id('User', user4.id)
    })
    expected = {'data': {'creator': {'avatar': 'https://some.pic/url/4/',
                                     'bio': 'test bio 4',
                                     'firstName': 'tuser4',
                                     'lastName': 'tlastname4',
                                     'username': None,
                                     'followerCount': 0,
                                     'isCreator': False,
                                     'themeGroups': {'edges': []}}}}
    assert res == expected


def test_get_noncreator_profile_anonymous(
        graphql_client_anonymous,
        user4,
):
    res = graphql_client_anonymous.post(creator_profile_query, variables={
        'userId': Node.to_global_id('User', user4.id)
    })
    expected = {'data': {'creator': None}}
    assert res == expected


creator_profile_by_username_query = '''
  query($username: String!) {
    creator(username: $username) {
        firstName
        lastName
        username
        avatar
        isCreator
        bio
        followerCount
        themeGroups {
          edges {
            node {
              title
              description
              isActive
              isPromoted
              sortOrder
              themes {
                edges {
                  node {
                    title
                    image
                    shortDescription
                    sortOrder
                    isSelected
                    contentBlocks {
                      image
                      text
                    }
                    exampleWines {
                      edges {
                        node {
                          sortOrder
                          name
                          image
                          description
                          location
                          highlights
                          varietals
                          price
                          brand
                          productUrl}}}}}}}}}}}
'''


def test_get_creator_profile_by_username(
        graphql_client_anonymous,
        user,
        user2,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
        theme_example_wine_1,
        theme_example_wine_2,
):
    expected_username = 'tuser4.tlastname4'

    assert user4.username == expected_username
    res = graphql_client_anonymous.post(creator_profile_by_username_query, variables={
        'username': user4.username
    })

    expected = {'data': {'creator': {
        'avatar': 'https://some.pic/url/4/',
        'bio': 'test bio 4',
        'firstName': 'tuser4',
        'lastName': 'tlastname4',
        'username': expected_username,
        'followerCount': 0,
        'isCreator': True,
        'themeGroups': {'edges': [
            {'node': {'description': 'theme group desc 3',
                      'isActive': True,
                      'isPromoted': True,
                      'sortOrder': 40,
                      'themes': {'edges': [
                          {'node': {
                              'contentBlocks': [{'image': 'image 1',
                                                 'text': 'text 1'},
                                                {'image': 'image 2',
                                                 'text': 'text 2'}],
                              'exampleWines': {'edges': [
                                  {'node': {'brand': 'brand 2',
                                            'description': 'desc 2',
                                            'highlights': ['h1', 'h2'],
                                            'image': 'https://wineimage.com/2',
                                            'location': 'location 2',
                                            'name': 'example wine 2',
                                            'price': '150.55',
                                            'productUrl': 'https://someproduct.url/2',
                                            'sortOrder': 11,
                                            'varietals': ['v1', 'v2']}},
                                  {'node': {'brand': 'brand 1',
                                            'description': 'desc 1',
                                            'highlights': ['h1', 'h2'],
                                            'image': 'https://wineimage.com/1',
                                            'location': 'location 1',
                                            'name': 'example wine 1',
                                            'price': '150',
                                            'productUrl': 'https://someproduct.url/1',
                                            'sortOrder': 22,
                                            'varietals': ['v1', 'v2']}}]},
                              'image': 'https://someimage4.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 4',
                              'sortOrder': 100,
                              'title': 'theme 4'}},
                          {'node': {
                              'contentBlocks': [],
                              'exampleWines': {'edges': []},
                              'image': 'https://someimage6.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 6',
                              'sortOrder': 200,
                              'title': 'theme 6'}},
                          {'node': {
                              'contentBlocks': [],
                              'exampleWines': {'edges': []},
                              'image': 'https://someimage5.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 5',
                              'sortOrder': 300,
                              'title': 'theme 5'}},
                          {'node': {
                              'contentBlocks': [],
                              'exampleWines': {'edges': []},
                              'image': 'https://someimage7.url',
                              'isSelected': False,
                              'shortDescription': 'theme short desc 7',
                              'sortOrder': 400,
                              'title': 'theme 7'}}]},
                      'title': 'theme group 3'}},
            {'node': {'description': 'theme group desc 4',
                      'isActive': True,
                      'isPromoted': False,
                      'sortOrder': 20,
                      'themes': {'edges': [
                          {'node': {'contentBlocks': [],
                                    'exampleWines': {'edges': []},
                                    'image': 'https://someimage9.url',
                                    'isSelected': False,
                                    'shortDescription': 'theme short desc 9',
                                    'sortOrder': 1000,
                                    'title': 'theme 9'}},
                          {'node': {'contentBlocks': [],
                                    'exampleWines': {'edges': []},
                                    'image': 'https://someimage8.url',
                                    'isSelected': False,
                                    'shortDescription': 'theme short desc 8',
                                    'sortOrder': 2000,
                                    'title': 'theme 8'}}]},
                      'title': 'theme group 4'}}]}}}}

    assert res == expected


def test_get_noncreator_profile_by_username_registered(
        graphql_client,
        user,
        user2,
        user4,
):
    populate_automatic_username(user4)
    assert user4.username == 'tuser4.tlastname4'
    res = graphql_client.post(creator_profile_by_username_query, variables={
        'username': user4.username
    })
    expected = {'data': {'creator': {'avatar': 'https://some.pic/url/4/',
                                     'bio': 'test bio 4',
                                     'firstName': 'tuser4',
                                     'lastName': 'tlastname4',
                                     'username': 'tuser4.tlastname4',
                                     'followerCount': 0,
                                     'isCreator': False,
                                     'themeGroups': {'edges': []}}}}
    assert res == expected


def test_get_noncreator_profile_by_username_anonymous(
        graphql_client_anonymous,
        user,
        user2,
        user4,
):
    populate_automatic_username(user4)
    assert user4.username == 'tuser4.tlastname4'
    res = graphql_client_anonymous.post(creator_profile_by_username_query, variables={
        'username': user4.username
    })
    assert res['data']['creator'] is None


user_selected_themes_order_by_selected_at_query = '''
query ($selected_themes_sort: SelectedThemesSortEnum!) {
  user {
    selectedThemes(sort: $selected_themes_sort) {
      edges {
        node {
          title
          image
          shortDescription
          sortOrder
          themeGroup {
            title
            description
            isActive
            isPromoted
            sortOrder
            user {
              firstName
              lastName}}}}}}}
'''


@patch('core.db.models.user.datetime')
def test_user_selected_themes_order_by_selected_at(
        datetime_m,
        graphql_client,
        user,
        user2,
        user4,
        theme_1,
        theme_2,
        theme_3,
        theme_4,
        theme_5,
        theme_6,
        theme_7,
        theme_8,
        theme_9,
        theme_10,
        empty_theme_group,
):
    datetime_m.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

    datetime_m.utcnow.return_value = datetime(2015, 6, 15, 13, 13, 13, 13)
    user.selected_themes.append(theme_9)
    db.session.commit()

    datetime_m.utcnow.return_value = datetime(2015, 6, 15, 13, 13, 13, 15)
    user.selected_themes.append(theme_2)
    db.session.commit()

    datetime_m.utcnow.return_value = datetime(2015, 6, 15, 13, 13, 13, 17)
    user.selected_themes.append(theme_1)
    db.session.commit()

    datetime_m.utcnow.return_value = datetime(2015, 6, 15, 13, 13, 13, 19)
    user.selected_themes.append(theme_5)
    db.session.commit()

    datetime_m.utcnow.return_value = datetime(2015, 6, 15, 13, 13, 13, 21)
    user.selected_themes.append(theme_6)
    db.session.commit()

    res = graphql_client.post(user_selected_themes_order_by_selected_at_query, variables={
        'selected_themes_sort': SORT_SELECTED_THEMES_SELECTED_AT_ASC
    })
    expected = {'data': {'user': {
        'selectedThemes': {'edges': [
            {'node': {'title': 'theme 9',
                      'shortDescription': 'theme short desc 9',
                      'image': 'https://someimage9.url',
                      'sortOrder': 1000,
                      'themeGroup': {'description': 'theme group desc 4',
                                     'isActive': True,
                                     'isPromoted': False,
                                     'sortOrder': 20,
                                     'title': 'theme group 4',
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 2',
                      'shortDescription': 'theme short desc 2',
                      'image': 'https://someimage2.url',
                      'sortOrder': 20,
                      'themeGroup': {'title': 'theme group 2',
                                     'description': 'theme group desc 2',
                                     'isActive': True,
                                     'isPromoted': False,
                                     'sortOrder': 30,
                                     'user': {'firstName': 'tuser2',
                                              'lastName': None}}, }},
            {'node': {'title': 'theme 5',
                      'shortDescription': 'theme short desc 5',
                      'image': 'https://someimage5.url',
                      'sortOrder': 300,
                      'themeGroup': {'title': 'theme group 3',
                                     'description': 'theme group desc 3',
                                     'isActive': True,
                                     'isPromoted': True,
                                     'sortOrder': 40,
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 6',
                      'shortDescription': 'theme short desc 6',
                      'image': 'https://someimage6.url',
                      'sortOrder': 200,
                      'themeGroup': {'description': 'theme group desc 3',
                                     'isActive': True,
                                     'isPromoted': True,
                                     'sortOrder': 40,
                                     'title': 'theme group 3',
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
        ]}}}}
    assert res == expected

    res = graphql_client.post(user_selected_themes_order_by_selected_at_query, variables={
        'selected_themes_sort': SORT_SELECTED_THEMES_SELECTED_AT_DESC
    })
    expected = {'data': {'user': {
        'selectedThemes': {'edges': [
            {'node': {'title': 'theme 6',
                      'shortDescription': 'theme short desc 6',
                      'image': 'https://someimage6.url',
                      'sortOrder': 200,
                      'themeGroup': {'description': 'theme group desc 3',
                                     'isActive': True,
                                     'isPromoted': True,
                                     'sortOrder': 40,
                                     'title': 'theme group 3',
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 5',
                      'shortDescription': 'theme short desc 5',
                      'image': 'https://someimage5.url',
                      'sortOrder': 300,
                      'themeGroup': {'title': 'theme group 3',
                                     'description': 'theme group desc 3',
                                     'isActive': True,
                                     'isPromoted': True,
                                     'sortOrder': 40,
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
            {'node': {'title': 'theme 2',
                      'shortDescription': 'theme short desc 2',
                      'image': 'https://someimage2.url',
                      'sortOrder': 20,
                      'themeGroup': {'title': 'theme group 2',
                                     'description': 'theme group desc 2',
                                     'isActive': True,
                                     'isPromoted': False,
                                     'sortOrder': 30,
                                     'user': {'firstName': 'tuser2',
                                              'lastName': None}}, }},
            {'node': {'title': 'theme 9',
                      'shortDescription': 'theme short desc 9',
                      'image': 'https://someimage9.url',
                      'sortOrder': 1000,
                      'themeGroup': {'description': 'theme group desc 4',
                                     'isActive': True,
                                     'isPromoted': False,
                                     'sortOrder': 20,
                                     'title': 'theme group 4',
                                     'user': {'firstName': 'tuser4',
                                              'lastName': 'tlastname4'}}, }},
        ]}}}}
    assert res == expected
