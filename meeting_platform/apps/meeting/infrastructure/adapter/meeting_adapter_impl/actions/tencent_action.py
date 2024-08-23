#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/19 16:16
# @Author  : Tom_zc
# @FileName: tencent_action.py
# @Software: PyCharm
from dataclasses import dataclass

from meeting.infrastructure.adapter.meeting_adapter_impl.actions.base_action import CreateAction, \
    UpdateAction, DeleteAction, GetParticipantsAction, GetVideoAction


@dataclass
class TencentCreateAction(CreateAction):
    date: str
    start: str
    end: str
    topic: str
    host_id: str
    is_record: bool


@dataclass
class TencentUpdateAction(UpdateAction):
    host_id: str
    mid: str
    date: str
    start: str
    end: str
    topic: str
    is_record: str


# noinspection SpellCheckingInspection
@dataclass
class TencentDeleteAction(DeleteAction):
    host_id: str
    mid: str
    mmid: str


# noinspection SpellCheckingInspection
@dataclass
class TencentGetParticipantsAction(GetParticipantsAction):
    host_id: str
    mmid: str


@dataclass
class TencentGetVideo(GetVideoAction):
    meeting: dict
