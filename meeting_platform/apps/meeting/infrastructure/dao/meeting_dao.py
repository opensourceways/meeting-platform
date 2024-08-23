#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:45
# @Author  : Tom_zc
# @FileName: meeting_adapter.py
# @Software: PyCharm
from meeting.models import Meeting


class MeetingDao(Meeting):

    @classmethod
    def get_conflict_meeting(cls, community, platform, date, start_search, end_search):
        return cls.objects.filter(community=community, platform=platform, is_delete=0,
                                  date=date, end__gt=start_search, start__lt=end_search)

    @classmethod
    def get_queryset(cls):
        return cls.objects.filter(is_delete=0)

    @classmethod
    def create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def get_by_id(cls, meeting_id):
        return cls.objects.filter(id=meeting_id, is_delete=0).first()

    @classmethod
    def update_by_id(cls, meeting_id, **kwargs):
        return cls.objects.filter(id=meeting_id, is_delete=0).update(**kwargs)

    @classmethod
    def delete_by_id(cls, meeting_id):
        return cls.objects.filter(id=meeting_id, is_delete=0).update(is_delete=1)
