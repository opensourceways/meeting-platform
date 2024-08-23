#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/20 19:51
# @Author  : Tom_zc
# @FileName: test_user.py
# @Software: PyCharm
from unittest import mock
from datetime import timedelta

from rest_framework import status
from rest_framework_simplejwt.tokens import Token

from app_meeting_server.test.openeuler.constant import xss_script, html_text, crlf_text
from app_meeting_server.test.openeuler.test_base import TestCommonUser
from app_meeting_server.utils.my_refresh import MyTokenObtainPairSerializer


class LoginViewTest(TestCommonUser):
    """the user login"""
    value = "*" * 16
    url = "/login/"

    def test_login_lack_code(self):
        """code is empty dict"""
        ret = self.client.post(self.url, data=dict())
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_over_length_code(self):
        """code is over length"""
        ret = self.client.post(self.url, data={"code": "*" * 129})
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_code(self):
        """invalid code"""
        for params in [xss_script, html_text, crlf_text]:
            ret = self.client.post(self.url, data={"code": params})
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inner_error(self):
        """request gitee failed"""
        ret = self.client.post(self.url, data={"code": "*" * 64})
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch("app_meeting_server.utils.wx_apis.wx_apis.get_openid")
    def test_login_openid_over_length_failed(self, mock_get_openid):
        """gitee name over length and operation mysql failed"""
        mock_get_openid.return_value = {}
        ret = self.client.post(self.url, data={"code": "*" * 64})
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)


class RefreshViewTest(TestCommonUser):
    """the user refresh token"""
    url = "/refresh/"

    def test_refresh_lack_refresh(self):
        """lack the refresh"""
        ret = self.client.post(self.url, data={})
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_not_match(self):
        """invalid refresh"""
        ret = self.client.post(self.url, data={"refresh": "match"})
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_expired(self):
        """token is expired"""
        _, _, user = self.create_user()
        Token.lifetime = timedelta()
        Token.token_type = "refresh"
        user_token = MyTokenObtainPairSerializer.get_token(user)
        self.update_user_refresh_signature(user.id, user_token)
        ret = self.client.post(self.url, data={"refresh": str(user_token)})
        self.assertEqual(ret.status_code, status.HTTP_200_OK)

    def test_refresh_ok(self):
        """all is ok"""
        _, refresh_token, user = self.create_user()
        ret = self.client.post(self.url, data={"refresh": refresh_token})
        self.assertEqual(ret.status_code, status.HTTP_200_OK)


class LogoutViewTest(TestCommonUser):
    """the user logout"""
    url = "/logout/"

    def test_logout_failed(self):
        """invalid token"""
        _, _, user = self.create_user()
        c = self.get_client("")
        ret = c.post(self.url)
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_ok(self):
        """all is ok"""
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)


class LogoffViewTest(TestCommonUser):
    """the user logoff"""
    url = "/logoff/"

    def test_logoff_failed(self):
        """failed by invalid token"""
        token, _, user = self.create_user()
        c = self.get_client("")
        ret = c.post(self.url)
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logoff_ok(self):
        """all is ok"""
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        _, user = self.get_user(user.openid)
        self.assertEqual(user.is_delete, 1)


class AgreePrivacyPolicyViewTest(TestCommonUser):
    """agree the agreement"""
    url = "/agree/"

    def test_agree_privacy_failed(self):
        """failed by invalid token"""
        self.create_user()
        c = self.get_client("")
        ret = c.put(self.url)
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_agree_privacy_ok(self):
        """all is ok"""
        header, _, user = self.create_user()
        c = self.get_client(header)
        ret = c.put(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        _, user = self.get_user(user.openid)
        self.assertEqual(user.agree_privacy_policy, True)


class RevokeAgreementViewTest(TestCommonUser):
    """revoke the agreement"""
    url = "/revoke/"

    def test_revoke_privacy_failed(self):
        """failed by invalid token"""
        self.create_user()
        c = self.get_client("")
        ret = c.post(self.url)
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revoke_agree_privacy_ok(self):
        """all is ok"""
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        _, user = self.get_user(user.openid)
        self.assertEqual(user.agree_privacy_policy, False)


class GroupsViewTest(TestCommonUser):
    """query group info"""
    url = "/groups/"

    def test_group_ok(self):
        group_names = ["group1", "group2"]
        for name in group_names:
            self.create_group(name)
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_maintainer_level(user.id)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_admin_level(user.id)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        data = ret.json()
        self.assertEqual(len(data), len(group_names))


class UsersIncludeViewTest(TestCommonUser):
    """the user is including in group"""
    url = "/users_include/{}/"

    def test_user_in_group_ok(self):
        group_name = "group1"
        count_user = 5
        group_obj = self.create_group(group_name)
        for i in range(count_user):
            _, _, user = self.create_user()
            self.create_group_user(user.id, group_name)
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_maintainer_level(user.id)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_admin_level(user.id)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        data = ret.json()
        self.assertEqual(len(data["data"]), count_user)


class UsersExcludeViewTest(TestCommonUser):
    """the user is excluding in group"""
    url = "/users_exclude/{}/"

    def test_user_in_not_in_group_ok(self):
        group_name = "group1"
        count_user = 5
        group_obj = self.create_group(group_name)
        for i in range(count_user):
            _, _, user = self.create_user()
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_maintainer_level(user.id)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_admin_level(user.id)
        ret = c.get(self.url.format(group_obj.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        data = ret.json()
        self.assertEqual(len(data["data"]), count_user)


class GroupUserAddViewTest(TestCommonUser):
    """add the user to group"""
    url = "/groupuser/action/new/"

    def test_add_user_to_group(self):
        group_name = "group1"
        count_user = 5
        user_ids = list()
        group_obj = self.create_group(group_name)
        for i in range(count_user):
            _, _, user = self.create_user()
            user_ids.append(user.id)
        data = {
            "group_id": group_obj.id,
            "ids": "-".join([str(user_id) for user_id in user_ids])
        }
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_maintainer_level(user.id)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_admin_level(user.id)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(ret.json()["code"], status.HTTP_200_OK)


class GroupUserDelViewTest(TestCommonUser):
    """remove the user from group"""
    url = "/groupuser/action/del/"

    def test_del_user_to_group(self):
        group_name = "group1"
        count_user = 5
        user_ids = list()
        group_obj = self.create_group(group_name)
        for i in range(count_user):
            _, _, user = self.create_user()
            self.create_group_user(user.id, group_name)
            user_ids.append(user.id)
        data = {
            "group_id": group_obj.id,
            "ids": "-".join([str(user_id) for user_id in user_ids])
        }
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_maintainer_level(user.id)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_admin_level(user.id)
        ret = c.post(self.url, data=data)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(ret.json()["code"], status.HTTP_200_OK)


class UserInfoViewTest(TestCommonUser):
    url = "/userinfo/{}/"

    def test_user_info(self):
        token, _, user = self.create_user()
        url = self.url.format(user.id)
        c = self.get_client(token)
        ret = c.get(url)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)


class SponsorsViewTest(TestCommonUser):
    url = "/sponsors/"

    def test_sponsors_view(self):
        count_user = 5
        for i in range(count_user):
            token, _, user = self.create_user()
            self.update_user_activity_maintainer_level(user.id)
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_activity_admin_level(user.id)
        ret = c.get(self.url)
        json_data = ret.json()
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json_data["data"]), count_user)


class NonSponsorViewTest(TestCommonUser):
    url = "/nonsponsors/"

    def test_non_sponsor_view(self):
        count_user = 5
        for i in range(count_user):
            token, _, user = self.create_user()
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_activity_admin_level(user.id)
        ret = c.get(self.url)
        json_data = ret.json()
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(len(json_data["data"]), count_user)


class SponsorAddViewTest(TestCommonUser):
    url = "/sponsor/action/new/"

    def test_sponsor_add_view(self):
        count_user = 5
        user_ids = list()
        for i in range(count_user):
            token, _, user = self.create_user()
            user_ids.append(user.id)
        body = {'ids': [str(user_id) for user_id in user_ids]}
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url, data=body)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.post(self.url, data=body)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_activity_admin_level(user.id)
        ret = c.post(self.url, data=body)
        json_data = ret.json()
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(json_data["code"], status.HTTP_200_OK)


class SponsorDelViewTest(TestCommonUser):
    url = "/sponsor/action/del/"

    def test_sponsor_add_view(self):
        count_user = 5
        user_ids = list()
        for i in range(count_user):
            token, _, user = self.create_user()
            self.update_user_activity_maintainer_level(user.id)
            user_ids.append(user.id)
        body = {'ids': [str(user_id) for user_id in user_ids]}
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.post(self.url, data=body)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.post(self.url, data=body)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_activity_admin_level(user.id)
        ret = c.post(self.url, data=body)
        json_data = ret.json()
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(json_data["code"], status.HTTP_200_OK)


class UpdateUserViewTest(TestCommonUser):
    url = "/user/{}/"

    def test_update_user_view(self):
        token, _, user = self.create_user()
        url = self.url.format(user.id)
        c = self.get_client(token)
        body = {
            "gitee_name": "test"
        }
        ret = c.put(url, data=body)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.put(url, data=body)
        self.assertEqual(ret.status_code, status.HTTP_403_FORBIDDEN)
        self.update_user_admin_level(user.id)
        ret = c.put(url, data=body)
        json_data = ret.json()
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        self.assertEqual(json_data["code"], status.HTTP_200_OK)


class UserGroupViewTest(TestCommonUser):
    url = "/usergroup/{}/"

    def test_user_group(self):
        group_name = "test1"
        group_obj = self.create_group(group_name)
        url = self.url.format(group_obj.id)
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(url)
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)


class MyCountsViewTest(TestCommonUser):
    url = "/mycounts/"

    def test_count_view(self):
        token, _, user = self.create_user()
        self.update_user_agree_policy(user.id)
        c = self.get_client(token)
        ret = c.get(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
