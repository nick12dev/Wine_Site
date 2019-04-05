# pylint: disable=unused-argument,bad-continuation,too-many-arguments,fixme
from unittest.mock import (
    patch,
    MagicMock,
)
import re

from graphene import Node

from core.db.models import db
from core.db.models.pipeline_sequence import PipelineSequence

integration_url_regex = re.compile(r'https://m3-integration-test\.com/api/1/source/(\d+)/sync/')

pipeline_sequence_list_query = '''
    query ($offset: Int, $first: Int, $sort: [PipelineSequenceSortEnum]) {
      scheduleManagement {
        pipelineSequences(offset: $offset, first: $first, sort: $sort) {
          totalCount
          edges {
            node {
              id
              source {
                name
              }
              state
              startTime
              endTime
              isActive
              isFullActive
              isUpdateActive
              isFullInProgress
              isUpdateInProgress
              comments}}}}}
'''


def test_pipeline_sequence_list_nonadmin(
        graphql_client, proposed_to_user_offer_item, accepted_order, completed_orders
):
    res = graphql_client.post(pipeline_sequence_list_query)
    assert res['data']['scheduleManagement'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']


def test_pipeline_sequence_list_default_order(
        graphql_client_admin,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_2 = pipeline_sequence_2.id
    ps_id_3 = pipeline_sequence_3.id
    ps_id_5 = pipeline_sequence_5.id

    res = graphql_client_admin.post(pipeline_sequence_list_query, variables={
        'offset': 1,
        'first': 3,
    })

    expected = {'data': {'scheduleManagement': {'pipelineSequences': {'edges': [
        {'node': {'comments': 'comments2',
                  'id': Node.to_global_id('PipelineSequence', ps_id_2),
                  'source': {'name': 'source_2'},
                  'isActive': False,
                  'isFullActive': False,
                  'isUpdateActive': False,
                  'isFullInProgress': False,
                  'isUpdateInProgress': False,
                  'startTime': '2018-02-15T21:30:13.000155',
                  'endTime': '2018-02-15T21:30:16.000295',
                  'state': 'error'}},
        {'node': {'comments': 'comments3',
                  'id': Node.to_global_id('PipelineSequence', ps_id_3),
                  'source': {'name': 'source_3'},
                  'isActive': True,
                  'isFullActive': True,
                  'isUpdateActive': False,
                  'isFullInProgress': True,
                  'isUpdateInProgress': False,
                  'startTime': '2018-01-13T21:33:13.000153',
                  'endTime': '2018-01-13T21:33:16.000235',
                  'state': 'queued'}},
        {'node': {'comments': 'comments5',
                  'id': Node.to_global_id('PipelineSequence', ps_id_5),
                  'source': {'name': 'source_no_shipping'},
                  'isActive': False,
                  'isFullActive': False,
                  'isUpdateActive': False,
                  'isFullInProgress': False,
                  'isUpdateInProgress': False,
                  'startTime': '2017-01-15T21:30:13.000155',
                  'endTime': '2017-01-15T21:30:16.000295',
                  'state': 'ready'}},
    ], 'totalCount': 5}}}}

    assert res == expected


def test_pipeline_sequence_list_order_by_end_time_desc(
        graphql_client_admin,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_1 = pipeline_sequence_1.id
    ps_id_3 = pipeline_sequence_3.id
    ps_id_4 = pipeline_sequence_4.id

    res = graphql_client_admin.post(pipeline_sequence_list_query, variables={
        'offset': 1,
        'first': 3,
        'sort': 'end_time_desc',
    })

    expected = {'data': {'scheduleManagement': {'pipelineSequences': {'edges': [
        {'node': {'comments': 'comments1',
                  'id': Node.to_global_id('PipelineSequence', ps_id_1),
                  'source': {'name': 'source_1'},
                  'isActive': True,
                  'isFullActive': True,
                  'isUpdateActive': False,
                  'isFullInProgress': False,
                  'isUpdateInProgress': False,
                  'startTime': '2018-01-15T21:30:13.000155',
                  'endTime': '2018-01-15T21:30:16.000295',
                  'state': 'state1'}},
        {'node': {'comments': 'comments4',
                  'id': Node.to_global_id('PipelineSequence', ps_id_4),
                  'source': {'name': 'source_source_4'},
                  'isActive': True,
                  'isFullActive': True,
                  'isUpdateActive': False,
                  'isFullInProgress': False,
                  'isUpdateInProgress': False,
                  'startTime': '2018-01-14T21:30:13.000155',
                  'endTime': '2018-01-14T21:30:16.000295',
                  'state': 'ready'}},
        {'node': {'comments': 'comments3',
                  'id': Node.to_global_id('PipelineSequence', ps_id_3),
                  'source': {'name': 'source_3'},
                  'isActive': True,
                  'isFullActive': True,
                  'isUpdateActive': False,
                  'isFullInProgress': True,
                  'isUpdateInProgress': False,
                  'startTime': '2018-01-13T21:33:13.000153',
                  'endTime': '2018-01-13T21:33:16.000235',
                  'state': 'queued'}},
    ], 'totalCount': 5}}}}

    assert res == expected


run_pipeline_sequence_query = '''
    mutation ($input: RunPipelineSequenceInput!) {
      runPipelineSequence(input: $input) {
        clientMutationId
        pipelineSequence {
          id
          source {
            name
          }
          state
          startTime
          endTime
          isActive
          isFullActive
          isUpdateActive
          isFullInProgress
          isUpdateInProgress
          comments}}}
'''


@patch('core.graphql.schemas.pipeline_sequence.requests')
def test_run_pipeline_sequence_nonadmin(
        requests_m,
        graphql_client,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_3 = Node.to_global_id('PipelineSequence', pipeline_sequence_3.id)

    res = graphql_client.post(run_pipeline_sequence_query, variables={
        'input': {
            'clientMutationId': 'testmutation',
            'id': ps_id_3,
        },
    })

    assert res['data']['runPipelineSequence'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']
    requests_m.get.assert_not_called()


def _run_pipeline_sequence_requests_get_mock(url, *args, **kwargs):
    source_id = int(integration_url_regex.match(url).group(1))
    pipeline_sequence = PipelineSequence.query.filter(
        PipelineSequence.source_id == source_id
    ).one()

    pipeline_sequence.state = 'queued'
    db.session.commit()

    result_mock = MagicMock()
    result_mock.text.return_value = 'test ok'
    result_mock.json.return_value = {}
    return result_mock


@patch('core.graphql.schemas.pipeline_sequence.requests')
def test_run_pipeline_sequence(
        requests_m,
        graphql_client_admin,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    requests_m.get.side_effect = _run_pipeline_sequence_requests_get_mock

    ps_id_4 = Node.to_global_id('PipelineSequence', pipeline_sequence_4.id)
    ps_source_id_4 = pipeline_sequence_4.source_id

    res = graphql_client_admin.post(run_pipeline_sequence_query, variables={
        'input': {
            'clientMutationId': 'testmutation',
            'id': ps_id_4,
        },
    })

    requests_m.get.assert_called_once_with(
        f'https://m3-integration-test.com/api/1/source/{ps_source_id_4}/sync/'
    )
    expected = {'data': {'runPipelineSequence': {
        'clientMutationId': 'testmutation',
        'pipelineSequence': {'comments': 'comments4',
                             'id': ps_id_4,
                             'source': {'name': 'source_source_4'},
                             'isActive': True,
                             'isFullActive': True,
                             'isUpdateActive': False,
                             'isFullInProgress': True,
                             'isUpdateInProgress': False,
                             'startTime': '2018-01-14T21:30:13.000155',
                             'endTime': '2018-01-14T21:30:16.000295',
                             'state': 'queued'}}}}
    assert res == expected


save_pipeline_sequence_query = '''
    mutation ($input: SavePipelineSequenceInput!) {
      savePipelineSequence(input: $input) {
        clientMutationId
        pipelineSequence {
          id
          source {
            name
          }
          state
          startTime
          endTime
          isActive
          isFullActive
          isUpdateActive
          isFullInProgress
          isUpdateInProgress
          comments}}}
'''


def test_save_pipeline_sequence_nonadmin(
        graphql_client,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_3 = Node.to_global_id('PipelineSequence', pipeline_sequence_3.id)

    res = graphql_client.post(save_pipeline_sequence_query, variables={
        'input': {
            'clientMutationId': 'testmutation',
            'id': ps_id_3,
            'isFullActive': False,
            'isUpdateActive': True,
        },
    })

    assert res['data']['savePipelineSequence'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']


def test_save_pipeline_sequence(
        graphql_client_admin,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_3 = Node.to_global_id('PipelineSequence', pipeline_sequence_3.id)

    res = graphql_client_admin.post(save_pipeline_sequence_query, variables={
        'input': {
            'clientMutationId': 'testmutation',
            'id': ps_id_3,
            'isFullActive': False,
            'isUpdateActive': True,
        },
    })

    expected = {'data': {'savePipelineSequence': {
        'clientMutationId': 'testmutation',
        'pipelineSequence': {'comments': 'comments3',
                             'id': ps_id_3,
                             'source': {'name': 'source_3'},
                             'isActive': False,
                             'isFullActive': False,
                             'isUpdateActive': False,
                             'isFullInProgress': True,
                             'isUpdateInProgress': False,
                             'startTime': '2018-01-13T21:33:13.000153',
                             'endTime': '2018-01-13T21:33:16.000235',
                             'state': 'queued'}}}}

    assert res == expected


save_pipeline_schedules_query = '''
    mutation ($input: SavePipelineSchedulesInput!) {
      savePipelineSchedules(input: $input) {
        clientMutationId
        pipelineSchedules {
          id
          source {
            name
          }
          state
          startTime
          endTime
          isActive
          isFullActive
          isUpdateActive
          isFullInProgress
          isUpdateInProgress
          comments}}}
'''


def test_save_pipeline_schedules_nonadmin(
        graphql_client,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_2 = Node.to_global_id('PipelineSequence', pipeline_sequence_2.id)
    ps_id_3 = Node.to_global_id('PipelineSequence', pipeline_sequence_3.id)

    res = graphql_client.post(save_pipeline_schedules_query, variables={
        'input': {
            'clientMutationId': 'testmutation',
            'pipelineSchedules': [
                {
                    'id': ps_id_3,
                    'isFullActive': False,
                    'isUpdateActive': True,
                },
                {
                    'id': ps_id_2,
                    'isFullActive': True,
                    'isUpdateActive': False,
                },
            ],
        },
    })

    assert res['data']['savePipelineSchedules'] is None
    assert '401 Unauthorized' in res['errors'][0]['message']


def test_save_pipeline_schedules(
        graphql_client_admin,
        pipeline_sequence_3,
        pipeline_sequence_1,
        pipeline_sequence_2,
        pipeline_sequence_4,
        pipeline_sequence_5,
):
    ps_id_2 = Node.to_global_id('PipelineSequence', pipeline_sequence_2.id)
    ps_id_3 = Node.to_global_id('PipelineSequence', pipeline_sequence_3.id)

    res = graphql_client_admin.post(save_pipeline_schedules_query, variables={
        'input': {
            'clientMutationId': 'testmutation',
            'pipelineSchedules': [
                {
                    'id': ps_id_3,
                    'isFullActive': False,
                    'isUpdateActive': True,
                },
                {
                    'id': ps_id_2,
                    'isFullActive': True,
                    'isUpdateActive': False,
                },
            ],
        },
    })

    expected = {'data': {'savePipelineSchedules': {
        'clientMutationId': 'testmutation',
        'pipelineSchedules': [
            {
                'comments': 'comments3',
                'id': ps_id_3,
                'source': {'name': 'source_3'},
                'isActive': False,
                'isFullActive': False,
                'isUpdateActive': False,
                'isFullInProgress': True,
                'isUpdateInProgress': False,
                'startTime': '2018-01-13T21:33:13.000153',
                'endTime': '2018-01-13T21:33:16.000235',
                'state': 'queued'
            },
            {
                'comments': 'comments2',
                'id': ps_id_2,
                'source': {'name': 'source_2'},
                'isActive': True,
                'isFullActive': True,
                'isUpdateActive': False,
                'isFullInProgress': False,
                'isUpdateInProgress': False,
                'startTime': '2018-02-15T21:30:13.000155',
                'endTime': '2018-02-15T21:30:16.000295',
                'state': 'error'
            },
        ]}}}

    assert res == expected
