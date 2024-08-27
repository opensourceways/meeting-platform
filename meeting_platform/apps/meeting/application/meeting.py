#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:59
# @Author  : Tom_zc
# @FileName: meeting.py
# @Software: PyCharm
import datetime
import logging
import secrets
import traceback

from django.conf import settings
from django.forms import model_to_dict

from meeting_platform.utils.common import start_thread, get_cur_date
from meeting_platform.utils.operation_log import set_log_thread_local, log_key
from meeting_platform.utils.ret_api import MyValidationError
from meeting_platform.utils.ret_code import RetCode
from meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl import MeetingAdapterImpl
from meeting.infrastructure.dao import meeting_dao
from meeting.infrastructure.adapter.message_adapter_impl.email_adapter_impl import CreateMessageEmailAdapterImpl, \
    DeleteMessageEmailAdapterImpl, UpdateMessageEmailAdapterImpl
from meeting.infrastructure.adapter.message_adapter_impl.kafka_adapter_impl import CreateMessageKafKaAdapterImpl, \
    DeleteMessageKafKaAdapterImpl, UpdateMessageKafKaAdapterImpl

logger = logging.getLogger("log")


class MeetingApp:
    meeting_dao = meeting_dao.MeetingDao
    meeting_adapter_impl = MeetingAdapterImpl()
    create_message_adapter_impl = [CreateMessageEmailAdapterImpl, CreateMessageKafKaAdapterImpl]
    update_message_adapter_impl = [UpdateMessageEmailAdapterImpl, UpdateMessageKafKaAdapterImpl]
    delete_message_adapter_impl = [DeleteMessageEmailAdapterImpl, DeleteMessageKafKaAdapterImpl]

    def _get_and_check_conflict_meetings_by_date(self, meeting):
        """check the conflict the meeting, if not conflict and return meeting"""
        community = meeting["community"]
        platform = meeting["platform"]
        date = meeting["date"]
        start = meeting["start"]
        end = meeting["end"]
        start_search = datetime.datetime.strftime(
            (datetime.datetime.strptime(start, '%H:%M') - datetime.timedelta(minutes=30)),
            '%H:%M')
        end_search = datetime.datetime.strftime(
            (datetime.datetime.strptime(end, '%H:%M') + datetime.timedelta(minutes=30)),
            '%H:%M')
        meetings = self.meeting_dao.get_conflict_meeting(community, platform, date,
                                                         start_search, end_search).values()
        unavailable_host_ids = [meeting['host_id'] for meeting in meetings]
        host_info = settings.COMMUNITY_HOST[meeting["community"]]["platform"]
        host_list = [key["HOST"] for key in host_info]
        available_host_id = list(set(host_list) - set(unavailable_host_ids))
        if len(available_host_id) == 0:
            logger.info('[MeetingApp/_get_and_check_conflict_meetings_by_date] '
                        '{}/{}: no available host'.format(meeting["community"], meeting["platform"]))
            raise MyValidationError(RetCode.STATUS_MEETING_DATE_CONFLICT)
        return available_host_id

    def _is_in_prepare_meeting_duration_before_meeting(self, meeting):
        start_date_str = "{} {}".format(meeting["date"], meeting["start"])
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
        if int((start_date - get_cur_date()).total_seconds()) < 60 * 60:
            raise MyValidationError(RetCode.STATUS_MEETING_CANNOT_BE_DELETE)

    def _send_message(self, meeting, message_handler):
        """send the message"""
        for handler in message_handler:
            try:
                handler.send_message(meeting)
            except Exception as e:
                logger.error("[MeetingApp/_send_message] err:{}, and traceback:{}".format(e, traceback.format_exc()))

    def create(self, meeting):
        """create meeting"""
        # check meeting-conflict
        available_host_id = self._get_and_check_conflict_meetings_by_date(meeting)
        meeting["host_id"] = secrets.choice(available_host_id)
        # create meeting
        meeting["mm_id"], meeting["mid"], meeting["join_url"] = self.meeting_adapter_impl.create(meeting["host_id"],
                                                                                                 meeting)
        # create in database
        result = self.meeting_dao.create(**meeting)
        # send message
        start_thread(self._send_message, (meeting, self.create_message_adapter_impl))
        logger.info('[MeetingApp/create] {}/{}: create meeting which mid is {} and id is {}.'.
                    format(meeting["community"], meeting["platform"], meeting["mid"], result))
        return result

    def update(self, meeting_id, meeting_data):
        """update meeting"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/update]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting = model_to_dict(meeting)
        meeting.update(meeting_data)
        meeting.update({"sequence": meeting["sequence"] + 1})
        # check meeting-conflict
        self._get_and_check_conflict_meetings_by_date(meeting)
        # check not update in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting)
        # update meeting
        self.meeting_adapter_impl.update(meeting)
        # update in database
        result = self.meeting_dao.update_by_id(meeting_id, **meeting)
        # send message
        start_thread(self._send_message, (meeting, self.update_message_adapter_impl))
        logger.info('[MeetingApp/update] {}/{}: update meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting["id"]))
        return result

    def delete(self, request, meeting_id):
        """delete meeting"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/delete]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        set_log_thread_local(request, log_key, [meeting["community"], meeting["topic"], meeting_id])
        meeting = model_to_dict(meeting)
        meeting.update({"sequence": meeting["sequence"] + 1})
        # check not delete in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting)
        # delete meeting
        self.meeting_adapter_impl.delete(meeting)
        # update is_delete=1 in database
        result = self.meeting_dao.delete_by_id(meeting_id)
        # send message
        start_thread(self._send_message, (meeting, self.delete_message_adapter_impl))
        logger.info('[MeetingApp/delete] {}/{}: delete meeting which mid is {} and id is {}.'
                    .format(meeting["community"], meeting["platform"], meeting["mid"], meeting_id))
        return result

    def get_participants(self, meeting_id):
        """get participants"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/get_participants]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        return self.meeting_adapter_impl.get_participants(model_to_dict(meeting))
