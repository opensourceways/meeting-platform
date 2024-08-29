#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/16 11:16
# @Author  : Tom_zc
# @FileName: models.py.py
# @Software: PyCharm
from django.contrib.auth.models import AbstractUser
from django.db import models

from meeting.domain.primitive.upload_status import UploadStatus


class User(AbstractUser):
    """user model"""

    class Meta:
        db_table = "user"
        verbose_name = "user"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class Meeting(models.Model):
    """meeting model"""
    sponsor = models.CharField(verbose_name='发起者', max_length=64)
    group_name = models.CharField(verbose_name='发起者所属SIG', max_length=64)
    community = models.CharField(verbose_name="发起者所在社区", max_length=16)
    topic = models.CharField(verbose_name='会议主题', max_length=128)
    platform = models.CharField(verbose_name="会议所属平台", max_length=16)
    date = models.CharField(verbose_name='会议日期', max_length=32)
    start = models.CharField(verbose_name='会议开始时间', max_length=32)
    end = models.CharField(verbose_name='会议结束时间', max_length=32)
    agenda = models.TextField(verbose_name='会议议程', default='', null=True, blank=True)
    etherpad = models.CharField(verbose_name='会议纪要etherpad', max_length=256, null=True, blank=True)
    email_list = models.TextField(verbose_name='邮件列表', null=True, blank=True)
    host_id = models.EmailField(verbose_name='会议host_id', null=True, blank=True)
    mid = models.CharField(verbose_name='会议id', max_length=32)
    m_mid = models.CharField(verbose_name='腾讯会议id', max_length=32, null=True, blank=True)
    join_url = models.CharField(verbose_name='进入会议url', max_length=128, null=True, blank=True)
    is_record = models.BooleanField(verbose_name="是否录制", default=False)
    upload_status = models.SmallIntegerField(verbose_name="上传状态", choices=UploadStatus.to_tuple(), default=0)
    replay_url = models.CharField(verbose_name='回放会议url', max_length=128, null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True, null=True, blank=True)
    update_time = models.DateTimeField(verbose_name='修改时间', null=True, blank=True)
    sequence = models.IntegerField(verbose_name='修改次数', default=1)
    is_delete = models.BooleanField(verbose_name='是否删除', default=False)

    objects = models.Manager()

    class Meta:
        db_table = "meetings"
        verbose_name = "meetings"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "{}/{}/{}".format(self.community, self.mid, self.topic)
