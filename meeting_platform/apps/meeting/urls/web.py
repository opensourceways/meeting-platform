#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 11:22
# @Author  : Tom_zc
# @FileName: web.py
# @Software: PyCharm

from django.urls import path

from meeting.controller.web import MeetingView, SingleMeetingView

urlpatterns = [
    path('meeting/', MeetingView.as_view()),  # 会议列表
    path('meeting/<int:id>/', SingleMeetingView.as_view()),  # 查询单个会议
]
