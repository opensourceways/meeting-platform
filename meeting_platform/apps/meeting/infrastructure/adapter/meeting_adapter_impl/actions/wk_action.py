#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 20:29
# @Author  : Tom_zc
# @FileName: wk_action.py
# @Software: PyCharm
from dataclasses import dataclass

from meeting.infrastructure.adapter.meeting_adapter_impl.actions.base_action import CreateAction, \
    UpdateAction, DeleteAction, GetParticipantsAction, GetVideoAction


@dataclass
class WkCreateAction(CreateAction):
    date: str
    start: str
    end: str
    topic: str
    host_id: str
    is_record: str


@dataclass
class WkUpdateAction(UpdateAction):
    host_id: str
    mid: str
    date: str
    start: str
    end: str
    topic: str
    is_record: str


@dataclass
class WkDeleteAction(DeleteAction):
    host_id: str
    mid: str


@dataclass
class WkGetParticipantsAction(GetParticipantsAction):
    host_id: str
    mid: str
    date: str
    start: str
    end: str


@dataclass
class WkGetVideo(GetVideoAction):
    meeting: dict
