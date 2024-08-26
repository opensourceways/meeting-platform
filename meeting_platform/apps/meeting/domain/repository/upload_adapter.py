#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/26 15:01
# @Author  : Tom_zc
# @FileName: upload_adapter.py
# @Software: PyCharm

from abc import ABC, abstractmethod


class UploadAdapter(ABC):
    def __init__(self, meeting):
        self.meeting = meeting

    @abstractmethod
    def upload(self, *args, **kwargs):
        raise NotImplementedError
