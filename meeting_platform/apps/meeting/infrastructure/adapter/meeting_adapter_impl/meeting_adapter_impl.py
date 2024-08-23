#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/10 14:30
# @Author  : Tom_zc
# @FileName: libs.py
# @Software: PyCharm
from django.forms import model_to_dict

from meeting.infrastructure.adapter.meeting_adapter_impl.actions.tencent_action import TencentCreateAction, \
    TencentDeleteAction, TencentGetParticipantsAction, TencentGetVideo, TencentUpdateAction
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.wk_action import WkCreateAction, WkUpdateAction, \
    WkDeleteAction, WkGetParticipantsAction, WkGetVideo
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.zoom_action import ZoomCreateAction, ZoomUpdateAction, \
    ZoomDeleteAction, ZoomGetParticipantsAction, ZoomGetVideo
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.tencent_api import TencentApi
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.wk_api import WkApi
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.zoom_api import ZoomApi


class MeetingAdapterImpl:

    def get_create_action(self, platform, host_id, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentCreateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                host_id=host_id,
                is_record=meeting["is_record"]
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkCreateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                host_id=host_id,
                is_record=meeting["is_record"]
            )
        elif platform.lower() == ZoomApi.meeting_type:
            action = ZoomCreateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                host_id=host_id,
                is_record=meeting["is_record"]
            )
        else:
            raise RuntimeError("[MeetingAdapterImpl/get_create_action]invalid platform type")
        return action

    def get_update_action(self, platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentUpdateAction(
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"],
                topic=meeting["topic"],
                host_id=meeting["host_id"],
                is_record=meeting["is_record"]
            )
        elif platform.lower() == WkApi.meeting_type:
            action = WkUpdateAction(
                host_id=meeting["host_id"],
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
            raise RuntimeError("invalid platform type")
        return action

    def get_delete_action(self, meeting):
        if meeting.mplatform.lower() == TencentApi.meeting_type:
            action = TencentDeleteAction(
                host_id=meeting["host_id"],
                mid=meeting["mid"],
                mmid=meeting["mm_id"],
            )
        elif meeting.mplatform.lower() == WkApi.meeting_type:
            action = WkDeleteAction(
                host_id=meeting["host_id"],
                mid=meeting["mid"]
            )
        elif meeting.mplatform.lower() == ZoomApi.meeting_type:
            action = ZoomDeleteAction(
                mid=meeting["mid"],
            )
        else:
            raise RuntimeError("invalid platform type")
        return action

    def get_participants_action(self, meeting):
        if meeting.platform.lower() == TencentApi.meeting_type:
            action = TencentGetParticipantsAction(
                host_id=meeting["host_id"],
                mmid=meeting["mm_id"],
            )
        elif meeting.platform.lower() == WkApi.meeting_type:
            action = WkGetParticipantsAction(
                host_id=meeting["host_id"],
                mid=meeting["mid"],
                date=meeting["date"],
                start=meeting["start"],
                end=meeting["end"])
        elif meeting.platform.lower() == ZoomApi.meeting_type:
            action = ZoomGetParticipantsAction(
                mid=meeting["mid"],
            )
        else:
            raise RuntimeError("invalid platform type")
        return action

    def get_video_action(self, meeting):
        if meeting.platform.lower() == TencentApi.meeting_type:
            action = TencentGetVideo(model_to_dict(meeting))
        elif meeting.platform.lower() == WkApi.meeting_type:
            action = WkGetVideo(model_to_dict(meeting))
        elif meeting.platform.lower() == ZoomApi.meeting_type:
            action = ZoomGetVideo(model_to_dict(meeting))
        else:
            raise RuntimeError("invalid platform type")
        return action
