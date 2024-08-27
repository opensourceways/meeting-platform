#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/27 11:50
# @Author  : Tom_zc
# @FileName: upload_status.py
# @Software: PyCharm
from meeting_platform.utils.base_enum import EnumBase


class UploadStatus(EnumBase):
    """上传状态"""
    INIT = (0, '初始化')
    UPLOAD_OBS = (1, '已经上传OBS')
    UPLOAD_BILI = (2, '已经上传BILI')
    UPLOAD_ALL = (10, '全部已经上传完成')
