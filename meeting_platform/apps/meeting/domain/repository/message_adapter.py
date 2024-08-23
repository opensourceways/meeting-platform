#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 15:04
# @Author  : Tom_zc
# @FileName: email_adapter.py
# @Software: PyCharm

from abc import ABC, abstractmethod


class MessageAdapter(ABC):
    @abstractmethod
    def send_message(self, *args, **kwargs):
        raise NotImplementedError
