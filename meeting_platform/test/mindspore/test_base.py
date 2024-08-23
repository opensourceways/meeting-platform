#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/20 20:05
# @Author  : Tom_zc
# @FileName: test_base.py
# @Software: PyCharm
import logging
import uuid
from contextlib import suppress

from rest_framework.test import APITestCase

from app_meeting_server.utils.common import get_uuid, refresh_token_and_refresh_token, make_refresh_signature, \
    get_version_params
from mindspore.models import Meeting, GroupUser, User, Group

logger = logging.getLogger("log")


class CommonClass:
    def clear_user(self):
        ret = GroupUser.objects.all().delete()
        logger.info("delete group user and result is:{}".format(str(ret)))
        ret = User.objects.all().delete()
        logger.info("delete user and result is:{}".format(str(ret)))

    def clear_group(self):
        ret = Group.objects.all().delete()
        logger.info("delete group and result is:{}".format(str(ret)))

    def clear_meetings(self):
        ret = Meeting.objects.all().delete()
        logger.info("delete meeting and result is:{}".format(str(ret)))

    def clear_meetings_by_id(self, meeting_id):
        ret = Meeting.objects.filter(id=meeting_id).update(is_delete=1)
        logger.info("delete meeting and result is:{}".format(str(ret)))

    def create_meetings(self, **kwargs):
        return Meeting.objects.create(**kwargs)

    def get_meetings_by_user_id(self, user_id):
        return Meeting.objects.get(user_id=user_id)

    def update_meetings(self, gitee_name, start_search, end_search):
        return Meeting.objects.filter(sponsor=gitee_name). \
            update(end__gt=start_search, start__lt=end_search)

    def format_token(self, token):
        return "Bearer {}".format(str(token))

    def get_gitee_name(self):
        return get_uuid()

    def get_group_name(self):
        while True:
            uid = uuid.uuid4()
            res = str(uid).split('-')[0]
            with suppress(ValueError):
                if Group.objects.filter(name='U_{}'.format(uid)):
                    raise ValueError('Duplicate group')
                return 'U_{}'.format(res)
            return 'U_{}'.format(res)

    def get_group(self, group_name):
        return Group.objects.get(name=group_name)

    def create_group(self, group_name):
        return Group.objects.create(name=group_name, group_type=1)

    def create_group_user(self, user_id, group_name):
        group = Group.objects.filter(name=group_name).first()
        return GroupUser.objects.create(group_id=group.id, user_id=user_id)

    def delete_group_user(self, user_id):
        return GroupUser.objects.filter(user_id=user_id).delete()

    def get_user(self, gitee_name):
        user = User.objects.get(gitee_name=gitee_name)
        access_token, _ = refresh_token_and_refresh_token(user)
        return access_token, user

    def get_user_by_gitee(self, gitee_name):
        return User.objects.get(gitee_name=gitee_name)

    def update_user_refresh_signature(self, user_id, refresh_token):
        refresh_signature = make_refresh_signature(refresh_token)
        User.objects.filter(id=user_id).update(refresh_signature=refresh_signature)

    def update_user_agree_policy(self, user_id):
        policy_version, app_policy_version, cur_date = get_version_params()
        User.objects.filter(id=user_id).update(agree_privacy_policy=True,
                                               agree_privacy_policy_time=cur_date,
                                               agree_privacy_policy_version=policy_version,
                                               agree_privacy_app_policy_version=app_policy_version
                                               )

    def update_user_admin_level(self, user_id):
        User.objects.filter(id=user_id).update(level=3)

    def update_user_maintainer_level(self, user_id):
        User.objects.filter(id=user_id).update(level=2)

    def create_user(self, gitee_name=None):
        if not gitee_name:
            gitee_name = self.get_gitee_name()
        user = User.objects.create(gitee_name=gitee_name)
        access_token, refresh_token = refresh_token_and_refresh_token(user)
        return access_token, refresh_token, user

    def create_maintainer_user(self, gitee_name=None):
        if not gitee_name:
            gitee_name = self.get_gitee_name()
        user = User.objects.create(
            gitee_name=gitee_name,
            level=2
        )
        access_token, _ = refresh_token_and_refresh_token(user)
        return access_token, user

    def create_admin_user(self, gitee_name=None):
        if not gitee_name:
            gitee_name = self.get_gitee_name()
        user = User.objects.create(
            gitee_name=gitee_name,
            level=3
        )
        access_token, _ = refresh_token_and_refresh_token(user)
        return access_token, user

    # noinspection PyUnresolvedReferences
    def get_client(self, token):
        c = self.client
        c.credentials(HTTP_AUTHORIZATION=self.format_token(token))
        return c

    # noinspection PyUnresolvedReferences
    def enable_client_auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=self.format_token(token))


class TestCommonUser(CommonClass, APITestCase):

    def tearDown(self):
        self.clear_user()


class TestCommonGroup(CommonClass, APITestCase):

    def tearDown(self):
        self.clear_group()


class TestCommonMeeting(CommonClass, APITestCase):
    pass
