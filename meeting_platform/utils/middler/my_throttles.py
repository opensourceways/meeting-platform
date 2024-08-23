#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/20 12:08
# @Author  : Tom_zc
# @FileName: my_throttles.py
# @Software: PyCharm
import time

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class MyAnonRateThrottle(AnonRateThrottle):
    def get_ident(self, request):
        return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


class MyUserRateThrottle(UserRateThrottle):
    def get_ident(self, request):
        return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")
