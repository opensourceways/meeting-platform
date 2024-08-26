#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/10 14:30
# @Author  : Tom_zc
# @FileName: libs.py
# @Software: PyCharm
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.tencent_action import TencentCreateAction, \
    TencentDeleteAction, TencentGetParticipantsAction, TencentGetVideo, TencentUpdateAction
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.wk_action import WkCreateAction, WkUpdateAction, \
    WkDeleteAction, WkGetParticipantsAction, WkGetVideo
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.zoom_action import ZoomCreateAction, \
    ZoomUpdateAction, ZoomDeleteAction, ZoomGetParticipantsAction, ZoomGetVideo
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.tencent_api import TencentApi
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.wk_api import WkApi
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.zoom_api import ZoomApi


class MeetingAdapterImpl:

    def get_create_action(self, platform, meeting):
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

    def get_update_action(self, platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentUpdateAction(
                mid=meeting["mid"],
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

    def get_delete_action(self, platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentDeleteAction(
                mid=meeting["mid"],
                mmid=meeting["mm_id"],
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

    def get_participants_action(self, platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentGetParticipantsAction(
                mmid=meeting["mm_id"],
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

    def get_video_action(self, platform, meeting):
        if platform.lower() == TencentApi.meeting_type:
            action = TencentGetVideo(
                mid=meeting["mid"],
                mmid=meeting["mmid"],
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
