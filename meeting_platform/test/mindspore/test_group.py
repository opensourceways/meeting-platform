#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/21 16:18
# @Author  : Tom_zc
# @FileName: test_group.py
# @Software: PyCharm
from rest_framework import status

from app_meeting_server.test.mindspore.test_base import TestCommonGroup


class GroupsViewTest(TestCommonGroup):
    url = "/groups/"

    def test_get_all_groups_failed_by_not_agree_policy(self):
        """maintainer get all groups"""
        self.create_group("group1")
        self.create_group("group2")
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_all_groups_failed_by_not_is_admin_or_maintainer(self):
        """maintainer get all groups"""
        self.create_group("group1")
        self.create_group("group2")
        token, _, user = self.create_user()
        self.update_user_agree_policy(user.id)
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_groups_ok_by_maintainer(self):
        """maintainer get all groups"""
        self.create_group("group1")
        self.create_group("group2")
        token, _, user = self.create_user()
        self.update_user_agree_policy(user.id)
        self.update_user_maintainer_level(user.id)
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)

    def test_get_all_groups_ok_by_admin(self):
        """admin get all groups"""
        self.create_group(self.get_group_name())
        self.create_group(self.get_group_name())
        token, _, user = self.create_user()
        self.update_user_agree_policy(user.id)
        self.update_user_admin_level(user.id)
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        json_data = ret.json()
        self.assertEqual(len(json_data["data"]), 2)
