#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 15:17
# @Author  : Tom_zc
# @FileName: obs_adapter.py
# @Software: PyCharm

from abc import ABC, abstractmethod


class ObsAdapter(ABC):
    @abstractmethod
    def get_object(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def list_objects(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def upload_file(self, *args, **kwargs):
        raise NotImplementedError
