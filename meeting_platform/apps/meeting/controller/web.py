#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:11
# @Author  : Tom_zc
# @FileName: web.py
# @Software: PyCharm
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView

from meeting_platform.utils.customized.my_pagination import MyPagination
from meeting_platform.utils.customized.my_view import MyRetrieveModelMixin, MyListModelMixin

from meeting.application.meeting import MeetingApp
from meeting.controller.serializers.meeting_serializers import MeetingSerializer, \
    SingleMeetingSerializer


class MeetingView(MyListModelMixin, GenericAPIView):
    """create or list meeting"""
    serializer_class = MeetingSerializer
    queryset = MeetingApp.meeting_dao.get_queryset()
    filter_backends = [SearchFilter]
    search_fields = ['community', "mid", "mm_id", "id"]
    pagination_class = MyPagination
    app_class = MeetingApp()


class SingleMeetingView(MyRetrieveModelMixin, GenericAPIView):
    """get or update or delete meeting"""
    lookup_field = "id"
    serializer_class = SingleMeetingSerializer
    queryset = MeetingApp.meeting_dao.get_queryset()
    app_class = MeetingApp()
