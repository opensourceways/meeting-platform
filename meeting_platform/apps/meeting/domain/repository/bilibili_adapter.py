#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 14:52
# @Author  : Tom_zc
# @FileName: bilibili_adapter.py
# @Software: PyCharm

from abc import ABC, abstractmethod


class BiliAdapter(ABC):
    @abstractmethod
    def upload(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def search_all_videos(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_replay_url(self, *args, **kwargs):
        raise NotImplementedError
