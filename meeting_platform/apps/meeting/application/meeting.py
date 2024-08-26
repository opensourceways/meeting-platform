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
from meeting_platform.utils.ret_api import MyValidationError, MyInnerError
from meeting_platform.utils.ret_code import RetCode
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.base_api import handler_meeting
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
        if int((start_date - get_cur_date()).total_seconds()) < 30 * 60:
            raise MyValidationError(RetCode.STATUS_MEETING_CANNOT_BE_DELETE)

    def _send_message(self, meeting, message_handler):
        """send the message"""
        for handler in message_handler:
            try:
                handler.send_message(meeting)
            except Exception as e:
                logger.error("[MeetingApp/_send_message] err:{}, and traceback:{}".format(e, traceback.format_exc()))

    def _create_meeting(self, host_id, meeting):
        action = self.meeting_adapter_impl.get_create_action(meeting["platform"], meeting)
        status, resp = handler_meeting(meeting["community"], meeting["platform"], host_id, action)
        if status not in [200, 201]:
            logger.error("[MeetingApp/_create_meeting] {}/{}: Failed to create meeting, and code is {}"
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_MEETING_FAILED_CREATE)
        meeting_id = resp.get("mmid")
        meeting_code = resp.get('mid')
        meeting_join_url = resp.get('join_url')
        return meeting_id, meeting_code, meeting_join_url

    def create(self, meeting):
        """create meeting"""
        available_host_id = self._get_and_check_conflict_meetings_by_date(meeting)
        meeting["host_id"] = secrets.choice(available_host_id)
        meeting["mm_id"], meeting["mid"], meeting["join_url"] = self._create_meeting(meeting["host_id"], meeting)
        result = self.meeting_dao.create(**meeting)
        logger.info('[MeetingApp/create] {}/{}: create meeting which mid is {}.'.format(meeting["community"],
                                                                                        meeting["platform"],
                                                                                        meeting["mid"]))
        start_thread(self._send_message, (meeting, self.create_message_adapter_impl))
        return result

    def _update_meeting(self, meeting):
        action = self.meeting_adapter_impl.get_update_action(meeting["platform"], meeting)
        status = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if status != 200:
            logger.error('[MeetingApp/_update_meeting] {}/{}: Failed to update meeting {}'
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_FAILED)

    def update(self, meeting_id, meeting_data):
        """update meeting"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/update]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting_dict = model_to_dict(meeting)
        meeting_dict.update(meeting_data)
        meeting_dict.update({"sequence": meeting_dict["sequence"] + 1})
        # check meeting-conflict
        self._get_and_check_conflict_meetings_by_date(meeting_dict)
        # not update in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting_dict)
        # update meeting
        self._update_meeting(meeting_dict)
        # sendmail
        start_thread(self._send_message, (meeting_dict, self.update_message_adapter_impl))
        # update is_delete=1 in database
        result = self.meeting_dao.update_by_id(meeting_id, **meeting_dict)
        logger.info('[MeetingApp/create] {}/{}: update meeting which mid is {}.'.format(meeting["community"],
                                                                                        meeting["platform"],
                                                                                        meeting["mid"]))
        return result

    def _delete_meeting(self, meeting):
        action = self.meeting_adapter_impl.get_delete_action(meeting["platform"], meeting)
        status = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if status != 200:
            logger.error('[MeetingApp/_delete_meeting] {}/{}: Failed to delete meeting {}'
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_FAILED)

    def delete(self, meeting_id):
        """delete meeting"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/delete]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        meeting = model_to_dict(meeting)
        meeting.update({"sequence": meeting["sequence"] + 1})
        # not delete in the before in start date
        self._is_in_prepare_meeting_duration_before_meeting(meeting)
        # delete meeting
        self._delete_meeting(meeting)
        # sendmail
        start_thread(self._send_message, (meeting, self.delete_message_adapter_impl))
        # update is_delete=1 in database
        result = self.meeting_dao.delete_by_id(meeting_id)
        logger.info('[MeetingApp/delete] {}/{}: delete meeting which mid is {}.'.format(meeting["community"],
                                                                                        meeting["platform"],
                                                                                        meeting["mid"]))
        return result

    def _get_participants(self, meeting):
        action = self.meeting_adapter_impl.get_participants_action(meeting["platform"], meeting)
        status = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if status != 200:
            logger.error('[MeetingApp/_get_participants] {}/{}: Failed to get participants {}'
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_FAILED)

    def get_participants(self, meeting_id):
        """get participants"""
        meeting = self.meeting_dao.get_by_id(meeting_id)
        if not meeting:
            logger.error('[MeetingApp/get_participants]Invalid meeting id:{}'.format(meeting_id))
            raise MyValidationError(RetCode.INFORMATION_CHANGE_ERROR)
        return self.get_participants(model_to_dict(meeting))
