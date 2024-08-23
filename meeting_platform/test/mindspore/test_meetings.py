#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/20 20:20
# @Author  : Tom_zc
# @FileName: test_meetings.py
# @Software: PyCharm
import copy
import datetime
import logging
import secrets
from copy import deepcopy
from unittest import mock

from rest_framework import status
from django.conf import settings

from app_meeting_server.test.mindspore.constant import xss_script, html_text, crlf_text
from app_meeting_server.test.mindspore.test_base import TestCommonMeeting
from app_meeting_server.utils.meeting_apis.actions.tencent_action import TencentDeleteAction
from app_meeting_server.utils.meeting_apis.apis.base_api import handler_meeting
from app_meeting_server.utils.ret_api import MyInnerError
from app_meeting_server.utils.ret_code import RetCode
from mindspore.models import Meeting

logger = logging.getLogger("log")
_invalid_params = [xss_script, html_text, crlf_text, ""]


class MeetingsMaintainerViewTest(TestCommonMeeting):
    url = "/meetings/"
    data = {
        "topic": "meeting unitest topic",  # string类型，会议名称，必填，长度限制128，限制内容中含有http，\r\n, xss攻击标签
        "sponsor": "Tom",  # string类型，会议发起人，必填，长度限制20，限制内容中含有http，\r\n, xss攻击标签
        "group_name": "group_temp",  # string类型，sig 组名称，必填， 限制40
        "mplatform": "tencent",  # string类型，平台，只能是以下参数: zoom,welink,tencent， 必填
        "date": str(datetime.datetime.now().date()),  # string类型，时间：2023-10-29，必填
        "start": "08:00",  # string类型，开始时间，必填
        "end": "09:00",  # string类型，结束时间，必填
        "etherpad": "{}/p/A-Tune-meetingsdafssdfadsfasdfa".format(settings.ETHERPAD_PREFIX),
        # string类型，以 https://etherpad.openeuler.org开头，必填，限制64
        "agenda": "今天开个会议",  # string类型，开会内容，必填，内容可以为空， 限制为4096，限制内容中含有http，\r\n, xss攻击标签
        # "emaillist": ";".join(["{}@163.com".format("a" * 42) for _ in range(20)]),
        "emaillist": "xxxxxxxxx@qq.com",
        # string类型, 发送邮件，以;拼接，长度最长为1000，每封邮箱长度最长为50，限制20封，必填，内容可以为空
        "record": True  # bool类型，是否自动录制，必填，可为空字符串，空字符串代表非自动录制，必填，内容可以为空
    }

    # noinspection DuplicatedCode
    def _setup(self):
        token, user = self.create_maintainer_user()
        self.update_user_agree_policy(user.id)
        self.update_user_maintainer_level(user.id)
        group_name = self.get_group_name()
        self.create_group(group_name)
        self.create_group_user(user.id, group_name)
        data = deepcopy(self.data)
        data["group_name"] = group_name
        data["sponsor"] = user.gitee_name
        cur_date = datetime.datetime.now()
        data["date"] = str(cur_date.date())
        start_date = cur_date + datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=3)
        data["start"] = "{}:15".format(start_date.hour)
        data["end"] = "{}:15".format(end_date.hour)
        self.enable_client_auth(token)
        return data

    def _teardown(self, data):
        sponsor = data["sponsor"]
        meetings = Meeting.objects.filter(sponsor=sponsor).all()
        logger.error("delete meetings:{}".format(meetings.count()))
        for meeting in meetings:
            token, user = self.get_user(sponsor)
            self.enable_client_auth(token)
            uri = MeetingDelViewTest.url.format(meeting.mid)
            self.client.delete(uri)
        self.clear_meetings()
        self.clear_group()
        self.clear_user()

    def get_invalid_params(self, data=None):
        fields = copy.deepcopy(_invalid_params)
        if data is not None:
            fields.append(data)
        return fields

    def test_params_topic_failed(self):
        data = self._setup()
        data["topic"] = '*' * 129
        ret = self.client.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for character in _invalid_params:
            data["topic"] = character
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_sponsor_failed(self):
        data = self._setup()
        fields = self.get_invalid_params("ddddd")
        fields.append("*" * 61)
        for params in fields:
            data["sponsor"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_platform_failed(self):
        data = self._setup()
        fields = self.get_invalid_params("ddddd")
        for params in fields:
            data["mplatform"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_group_name_failed(self):
        data = self._setup()
        fields = self.get_invalid_params("ddddd")
        for params in fields:
            data["group_name"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_etherpad_failed(self):
        data = self._setup()
        fields = self.get_invalid_params()
        for params in fields:
            data["etherpad"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    # noinspection SpellCheckingInspection
    def test_params_emaillist_failed(self):
        data = self._setup()
        fields = self.get_invalid_params()
        fields.extend([
            "sdajkfljlkdsjfk;asd@qq.com",
            ";".join(["{}@163.com".format("a" * 42) for _ in range(51)]),
            ";".join(["{}163.com".format("a" * 42) for _ in range(10)]),
        ])
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["emaillist"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_agenda_failed(self):
        data = self._setup()
        fields = self.get_invalid_params()
        for params in fields:
            if not params or params == crlf_text:
                continue
            data["agenda"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_record_failed(self):
        data = self._setup()
        fields = self.get_invalid_params()
        for params in fields:
            data["record"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_date_failed(self):
        data = self._setup()
        fields = self.get_invalid_params("08:1X")
        for params in fields:
            data["date"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_start_failed(self):
        data = self._setup()
        fields = self.get_invalid_params()
        for params in fields:
            data["start"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for params in ["07:15", "22:15", "15:10", "15:60", "15:-1"]:
            data["start"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_params_end_failed(self):
        data = self._setup()
        fields = self.get_invalid_params()
        for params in fields:
            data["end"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        for params in ["07:15", "23:15", "15:10", "15:60", "15:-1"]:
            data["end"] = params
            ret = self.client.post(self.url, data=data)
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_invalid_check_duration_failed(self):
        data = self._setup()
        cur_date = datetime.datetime.now()
        start_date = cur_date - datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=2)
        data["start"] = "{}:15".format(start_date.hour)
        data["end"] = "{}:15".format(end_date.hour)
        ret = self.client.post(self.url, data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        start_date = cur_date + datetime.timedelta(days=61)
        data["date"] = str(start_date.date())
        data["start"] = "10:15"
        data["end"] = "12:15"
        ret = self.client.post(self.url, data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        data["date"] = str(datetime.datetime.now().date())
        start_date = cur_date + datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=3)
        data["start"] = "{}:15".format(end_date.hour)
        data["end"] = "{}:15".format(start_date.hour)
        ret = self.client.post(self.url, data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    def test_no_permission_by_normal_user_failed(self):
        token, _, user = self.create_user()
        self.update_user_agree_policy(user.id)
        self.enable_client_auth(str(token))
        ret = self.client.post(self.url, data=self.data)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_is_not_in_group_failed(self):
        data = self._setup()
        data["community"] = "MindSpore"
        data["meeting_type"] = 1
        data["group_type"] = 1
        data["user_id"] = self.get_user_by_gitee(data["sponsor"]).id
        data["group_id"] = self.get_group(data["group_name"]).id
        user = self.get_user_by_gitee(data["sponsor"])
        self.delete_group_user(user.id)
        ret = self.client.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self._teardown(data)

    def test_conflict_meeting_failed(self):
        data = self._setup()
        data["community"] = "MindSpore"
        data["meeting_type"] = 1
        data["group_type"] = 1
        hosts_id = settings.MEETING_HOSTS.get(data["mplatform"])
        data["host_id"] = secrets.choice(hosts_id)
        data["user_id"] = self.get_user_by_gitee(data["sponsor"]).id
        data["group_id"] = self.get_group(data["group_name"]).id
        self.create_meetings(**data)
        ret = self.client.post(self.url, data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(data)

    @mock.patch("mindspore.views.CreateMeetingView._create_meeting_by_choice")
    def test_create_meeting_failed(self, mock_create_meeting_by_choice):
        data = self._setup()
        mock_create_meeting_by_choice.side_effect = MyInnerError(RetCode.STATUS_MEETING_FAILED_CREATE)
        ret = self.client.post(self.url, data)
        self._teardown(data)
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_meeting_ok(self):
        data = self._setup()
        ret = self.client.post(self.url, data)
        self._teardown(data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)


# noinspection DuplicatedCode
class MeetingsAdminViewTest(MeetingsMaintainerViewTest):

    def _setup(self):
        token, user = self.create_admin_user()
        self.update_user_agree_policy(user.id)
        self.update_user_admin_level(user.id)
        group_name = self.get_group_name()
        self.create_group(group_name)
        self.create_group_user(user.id, group_name)
        data = deepcopy(self.data)
        data["group_name"] = group_name
        data["sponsor"] = user.gitee_name
        cur_date = datetime.datetime.now()
        data["date"] = str(cur_date.date())
        start_date = cur_date + datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=3)
        data["start"] = "{}:15".format(start_date.hour)
        data["end"] = "{}:15".format(end_date.hour)
        self.enable_client_auth(token)
        return data

    def test_user_is_not_in_group_failed(self):
        pass


class MeetingDelViewTest(TestCommonMeeting):
    url = "/meetings/{}/"

    # noinspection DuplicatedCode
    def prepare_env(self):
        token, user = self.create_maintainer_user()
        self.update_user_agree_policy(user.id)
        self.update_user_maintainer_level(user.id)
        group_name = self.get_group_name()
        self.create_group(group_name)
        self.create_group_user(user.id, group_name)
        data = deepcopy(MeetingsMaintainerViewTest.data)
        data["group_name"] = group_name
        data["sponsor"] = user.gitee_name
        cur_date = datetime.datetime.now()
        data["date"] = str(cur_date.date())
        start_date = cur_date + datetime.timedelta(hours=2)
        end_date = cur_date + datetime.timedelta(hours=3)
        data["start"] = "{}:15".format(start_date.hour)
        data["end"] = "{}:15".format(end_date.hour)
        self.enable_client_auth(token)
        self.client.post(MeetingsMaintainerViewTest.url, data)
        return data

    def normal_test(self):
        create_user, meeting = self._setup()
        token, user = self.get_user(create_user.gitee_name)
        self.enable_client_auth(token)
        ret = self.client.delete(self.url.format(meeting.mid))
        return ret, meeting

    def _setup(self):
        data = self.prepare_env()
        token, user = self.get_user(data["sponsor"])
        self.enable_client_auth(token)
        meeting = self.get_meetings_by_user_id(user.id)
        return user, meeting

    def _teardown(self, meeting):
        action = TencentDeleteAction(
            host_id=meeting.host_id,
            mid=meeting.mid,
            mmid=meeting.mmid,
        )
        handler_meeting(meeting.mplatform, action)
        logger.error("delete meeting:{}".format(meeting.mid))

    def test_meeting_is_not_exist_failed(self):
        user, meeting = self._setup()
        self.clear_meetings_by_id(meeting.id)
        ret = self.client.delete(self.url.format(meeting.mid))
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self._teardown(meeting)

    def test_delete_not_create_by_owner(self):
        create_user, meeting = self._setup()
        token, user = self.create_maintainer_user()
        self.update_user_agree_policy(user.id)
        self.update_user_maintainer_level(user.id)
        self.enable_client_auth(token)
        ret = self.client.delete(self.url.format(meeting.mid))
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        token, user = self.get_user(create_user.gitee_name)
        self.enable_client_auth(token)
        ret = self.client.delete(self.url.format(meeting.mid))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)

    def test_delete_by_normal_user(self):
        create_user, meeting = self._setup()
        token, _, user = self.create_user()
        self.update_user_agree_policy(user.id)
        self.update_user_maintainer_level(user.id)
        self.enable_client_auth(token)
        ret = self.client.delete(self.url.format(meeting.mid))
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self._teardown(meeting)

    @mock.patch("mindspore.views.MeetingView._delete_meeting")
    def test_delete_failed(self, mock_delete_meeting):
        mock_delete_meeting.side_effect = MyInnerError(RetCode.STATUS_FAILED)
        ret, meeting = self.normal_test()
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self._teardown(meeting)

    def test_delete_ok(self):
        ret, meeting = self.normal_test()
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
