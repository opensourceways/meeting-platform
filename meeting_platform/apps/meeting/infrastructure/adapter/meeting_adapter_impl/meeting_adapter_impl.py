#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/10 14:30
# @Author  : Tom_zc
# @FileName: libs.py
# @Software: PyCharm
import logging

from meeting_platform.utils.ret_api import MyInnerError
from meeting_platform.utils.ret_code import RetCode
from meeting.domain.repository.meeting_adapter import MeetingAdapter
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.tencent_action import TencentCreateAction, \
    TencentDeleteAction, TencentGetParticipantsAction, TencentGetVideo, TencentUpdateAction
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.wk_action import WkCreateAction, WkUpdateAction, \
    WkDeleteAction, WkGetParticipantsAction, WkGetVideo
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.zoom_action import ZoomCreateAction, \
    ZoomUpdateAction, ZoomDeleteAction, ZoomGetParticipantsAction, ZoomGetVideo
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.base_api import handler_meeting
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.tencent_api import TencentApi
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.wk_api import WkApi
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.zoom_api import ZoomApi

logger = logging.getLogger("log")


class MeetingAction:

    @staticmethod
    def get_create_action(platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentCreateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                is_record=meeting["is_record"]
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkCreateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                is_record=meeting["is_record"]
            )
        elif platform.lower() == ZoomApi.meeting_type:
            action = ZoomCreateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                is_record=meeting["is_record"]
            )
        else:
            raise RuntimeError("[MeetingAdapterImpl/get_create_action] invalid platform type")
        return action

    # noinspection SpellCheckingInspection
    @staticmethod
    def get_update_action(platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentUpdateAction(
                mid=meeting["mid"],
                m_mid=meeting["m_mid"],
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                is_record=meeting["is_record"]
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkUpdateAction(
                mid=meeting["mid"],
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                is_record=meeting["is_record"],
            )
        elif platform.lower() == ZoomApi.meeting_type:
            action = ZoomUpdateAction(
                mid=meeting["mid"],
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                is_record=meeting["is_record"]
            )
        else:
            raise RuntimeError("[MeetingAdapterImpl/get_update_action] invalid platform type")
        return action

    @staticmethod
    def get_delete_action(platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentDeleteAction(
                mid=meeting["mid"],
                m_mid=meeting["m_mid"],
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkDeleteAction(
                mid=meeting["mid"]
            )
        elif platform.lower() == ZoomApi.meeting_type:
            action = ZoomDeleteAction(
                mid=meeting["mid"],
            )
        else:
            raise RuntimeError("[MeetingAdapterImpl/get_delete_action] invalid platform type")
        return action

    @staticmethod
    def get_participants_action(platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentGetParticipantsAction(
                m_mid=meeting["m_mid"],
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkGetParticipantsAction(
                mid=meeting["mid"],
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"])
        elif platform.lower() == ZoomApi.meeting_type:
            action = ZoomGetParticipantsAction(
                mid=meeting["mid"],
            )
        else:
            raise RuntimeError("[MeetingAdapterImpl/get_participants_action] invalid platform type")
        return action

    # noinspection SpellCheckingInspection
    @staticmethod
    def get_video_action(platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentGetVideo(
                mid=meeting["mid"],
                m_mid=meeting["m_mid"],
                date=meeting["date"],
                start=meeting["start"]
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkGetVideo(
                mid=meeting["mid"],
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
            )
        elif platform.lower() == ZoomApi.meeting_type:
            action = ZoomGetVideo(mid=meeting["mid"])
        else:
            raise RuntimeError("[MeetingAdapterImpl/get_video_action] invalid platform type")
        return action


class MeetingAdapterImpl(MeetingAdapter):
    meeting_action = MeetingAction

    def create(self, host_id, meeting):
        action = self.meeting_action.get_create_action(meeting["platform"], meeting)
        status, resp = handler_meeting(meeting["community"], meeting["platform"], host_id, action)
        if not str(status).startswith("20"):
            logger.error("[MeetingAdapterImpl/create] {}/{}: Failed to create meeting, and code is {}"
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_MEETING_FAILED_CREATE)
        meeting_id = resp.get('mid')
        meeting_mid = resp.get("m_mid")
        meeting_join_url = resp.get('join_url')
        return meeting_id, meeting_mid, meeting_join_url

    def update(self, meeting):
        action = self.meeting_action.get_update_action(meeting["platform"], meeting)
        status = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if not str(status).startswith("20"):
            logger.error('[MeetingAdapterImpl/update] {}/{}: Failed to update meeting {}'
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_MEETING_FAILED_UPDATE)

    def delete(self, meeting):
        action = self.meeting_action.get_delete_action(meeting["platform"], meeting)
        status = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if not str(status).startswith("20") and status != 404:
            logger.error('[MeetingAdapterImpl/delete] {}/{}: Failed to delete meeting {}'
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_FAILED)

    def get_participants(self, meeting):
        action = self.meeting_action.get_participants_action(meeting["platform"], meeting)
        status = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if not str(status).startswith("20"):
            logger.error('[MeetingAdapterImpl/get_participants] {}/{}: Failed to get participants {}'
                         .format(meeting["community"], meeting["platform"], str(status)))
            raise MyInnerError(RetCode.STATUS_FAILED)

    def get_video(self, meeting):
        action = self.meeting_action.get_video_action(meeting["platform"], meeting)
        return handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
