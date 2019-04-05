#
# pylint: disable=unused-argument,too-few-public-methods
import logging

import graphene
import requests
from graphene import relay
from sqlalchemy.orm import joinedload
from flask import current_app

from core.cognito import admin_user_permission
from core.dbmethods import fetch_schedules_by_ids
from core.graphql.schemas import (
    RegisteredUserObjectType,
    OptimizeResolveConnection,
    OptimizeResolveTuple,
    save_input_fields,
    create_sort_enum_for_model,
    CustomSortOrder,
    from_global_id_assert_type,
)
from core.graphql.schemas.source import Source
from core.db.models import db
from core.db.models.pipeline_sequence import PipelineSequence as PipelineSequenceModel


class PipelineSequence(RegisteredUserObjectType):
    class Meta:
        model = PipelineSequenceModel
        interfaces = (relay.Node,)
        only_fields = (
            'source',
            'state',
            'start_time',
            'end_time',
            'is_active',
            'comments',
        )

    is_full_active = graphene.Boolean()
    is_update_active = graphene.Boolean()
    is_full_in_progress = graphene.Boolean()
    is_update_in_progress = graphene.Boolean()

    @staticmethod
    def get_model_owner(model):
        return None

    @staticmethod
    def optimize_resolve_source(query_parent_path):
        query_child_path = '.'.join([query_parent_path, 'source'])

        return OptimizeResolveTuple(
            query_options=joinedload(query_child_path),
            query_child_path=query_child_path,
            child_node_class=Source
        )

    @staticmethod
    def resolve_is_full_active(model, info):
        return model.is_active

    @staticmethod
    def resolve_is_update_active(model, info):
        # TODO support is_update_active as well when it is available in m3-integration
        return False

    @staticmethod
    def resolve_is_full_in_progress(model, info):
        return model.state in ('queued', 'executing', 'aggregating')

    @staticmethod
    def resolve_is_update_in_progress(model, info):
        # TODO implement it when partial run is available in m3-integration
        return False


PipelineSequenceSortEnum = create_sort_enum_for_model(PipelineSequenceModel, custom_sort_orders=[
    CustomSortOrder(name='source_name_asc', value=None, is_asc=True),
    CustomSortOrder(name='source_name_desc', value=None, is_asc=False),
])


class PipelineSequencesConnection(OptimizeResolveConnection):
    class Meta:
        node = PipelineSequence


def _run_pipeline_sequence_full(source_id):
    url = f'{current_app.config["INTEGRATION_API_URL"]}/api/1/source/{source_id}/sync/'
    logging.info('calling integration api: "%s"', url)
    response = requests.get(url)
    logging.info('got response: %s', response.text)
    response.raise_for_status()
    return response.json()


class RunPipelineSequence(relay.ClientIDMutation):
    class Input:
        id = graphene.ID(required=True)

    pipeline_sequence = graphene.Field(PipelineSequence)

    @classmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def mutate_and_get_payload(cls, root, info, **inp):
        logging.info('RunPipelineSequence input: %s', inp)
        pipeline_sequence_id = from_global_id_assert_type(inp['id'], 'PipelineSequence')

        source_id = db.session.query(PipelineSequenceModel.source_id).filter(
            PipelineSequenceModel.id == pipeline_sequence_id
        ).first()[0]

        _run_pipeline_sequence_full(source_id)

        return RunPipelineSequence(
            pipeline_sequence=PipelineSequenceModel.query.get(pipeline_sequence_id)
        )


class SavePipelineSequence(relay.ClientIDMutation):
    # TODO get rid of this class in favor to SavePipelineSchedules when Admin is ready
    class Input:
        id = graphene.ID(required=True)
        is_full_active = graphene.Boolean()
        is_update_active = graphene.Boolean()

    pipeline_sequence = graphene.Field(PipelineSequence)

    @classmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def mutate_and_get_payload(cls, root, info, **inp):
        logging.info('SavePipelineSequence input: %s', inp)
        pipeline_sequence_id = from_global_id_assert_type(inp['id'], 'PipelineSequence')

        save_input_fields(
            inp,
            (('is_full_active', 'is_active'),),
            # TODO support is_update_active as well when it is available in m3-integration
            PipelineSequenceModel.query.get(pipeline_sequence_id),
        )
        db.session.commit()

        return SavePipelineSequence(
            pipeline_sequence=PipelineSequenceModel.query.get(pipeline_sequence_id)
        )


class PipelineScheduleInput(graphene.InputObjectType):
    id = graphene.ID(required=True)
    is_full_active = graphene.Boolean()
    is_update_active = graphene.Boolean()


class SavePipelineSchedules(relay.ClientIDMutation):
    class Input:
        pipeline_schedules = graphene.List(PipelineScheduleInput, required=True)

    pipeline_schedules = graphene.List(PipelineSequence)

    @classmethod
    @admin_user_permission.require(http_exception=401, pass_identity=False)
    def mutate_and_get_payload(cls, root, info, **inp):
        logging.info('SavePipelineSchedules input: %s', inp)

        schedule_inp_dict = {}
        for schedule_inp in inp['pipeline_schedules']:
            schedule_id = from_global_id_assert_type(schedule_inp['id'], 'PipelineSequence')

            schedule_inp_dict[schedule_id] = schedule_inp

        for schedule in fetch_schedules_by_ids(schedule_inp_dict.keys()):
            schedule_inp = schedule_inp_dict[schedule.id]

            save_input_fields(
                schedule_inp,
                (('is_full_active', 'is_active'),),
                # TODO support is_update_active as well when it is available in m3-integration
                schedule,
            )
        db.session.commit()

        return SavePipelineSchedules(
            pipeline_schedules=fetch_schedules_by_ids(schedule_inp_dict.keys())
        )
