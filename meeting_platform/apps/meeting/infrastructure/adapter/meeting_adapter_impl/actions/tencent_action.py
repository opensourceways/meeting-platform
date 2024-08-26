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
    is_record: bool


# noinspection SpellCheckingInspection
@dataclass
class TencentUpdateAction(UpdateAction):
    mid: str
    mmid: str
    date: str
    start: str
    end: str
    topic: str
    is_record: str


# noinspection SpellCheckingInspection
@dataclass
class TencentDeleteAction(DeleteAction):
    mid: str
    mmid: str


# noinspection SpellCheckingInspection
@dataclass
class TencentGetParticipantsAction(GetParticipantsAction):
    mmid: str


# noinspection SpellCheckingInspection
@dataclass
class TencentGetVideo(GetVideoAction):
    mid: str
    mmid: str
    date: str
    start: str
