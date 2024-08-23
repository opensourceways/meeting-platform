#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/20 19:51
# @Author  : Tom_zc
# @FileName: test_user.py
# @Software: PyCharm
from datetime import timedelta

from rest_framework import status
from unittest import mock
from rest_framework_simplejwt.tokens import Token

from app_meeting_server.test.mindspore.constant import xss_script, html_text, crlf_text
from app_meeting_server.test.mindspore.test_base import TestCommonUser
from app_meeting_server.utils.my_refresh import MyTokenObtainPairSerializer


class LoginViewTest(TestCommonUser):
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

    def test_login_empty_code(self):
        """code is empty"""
        ret = self.client.post(self.url, data={"code": ""})
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_invalid_code(self):
        """invalid code"""
        for params in [xss_script, html_text, crlf_text]:
            ret = self.client.post(self.url, data={"code": params})
            self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inner_error(self):
        """request gitee failed"""
        ret = self.client.post(self.url, data={"code": "*" * 64})
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @mock.patch("app_meeting_server.utils.client.gitee_client.GiteeClient.get_user_by_code")
    def test_login_gitee_name_over_length_failed(self, mock_get_user_by_code):
        """gitee name over length and operation mysql failed"""
        mock_get_user_by_code.return_value = "*" * 61
        ret = self.client.post(self.url, data={"code": "*" * 64})
        self.assertEqual(ret.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @mock.patch("app_meeting_server.utils.client.gitee_client.GiteeClient.get_user_by_code")
    def test_login_success_code(self, mock_get_user_by_code):
        """success"""
        mock_get_user_by_code.return_value = self.get_gitee_name()
        ret = self.client.post(self.url, data={"code": "*" * 64})
        self.assertEqual(ret.status_code, status.HTTP_200_OK)


class RefreshViewTest(TestCommonUser):
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
        _, user = self.get_user(user.gitee_name)
        self.assertEqual(user.is_delete, 1)


class AgreePrivacyPolicyViewTest(TestCommonUser):
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
        _, user = self.get_user(user.gitee_name)
        self.assertEqual(user.agree_privacy_policy, True)


class RevokeAgreementViewTest(TestCommonUser):
    url = "/revoke/"

    def test_revoke_privacy_failed(self):
        """failed by invalid token"""
        self.create_user()
        c = self.get_client("")
        ret = c.put(self.url)
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revoke_agree_privacy_ok(self):
        """all is ok"""
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.put(self.url)
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        _, user = self.get_user(user.gitee_name)
        self.assertEqual(user.agree_privacy_policy, False)


class UserInfoViewTest(TestCommonUser):
    url = "/userinfo/{}/"

    def test_user_info_failed(self):
        """failed by invalid token"""
        _, _, user = self.create_user()
        c = self.get_client("")
        ret = c.get(self.url.format(user.id))
        self.assertEqual(ret.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_info_ok(self):
        """all is ok"""
        token, _, user = self.create_user()
        c = self.get_client(token)
        ret = c.get(self.url.format(user.id))
        self.assertEqual(ret.status_code, status.HTTP_400_BAD_REQUEST)
        self.update_user_agree_policy(user.id)
        ret = c.get(self.url.format(user.id))
        self.assertEqual(ret.status_code, status.HTTP_200_OK)
        data = ret.json()
        self.assertEqual(data["data"]["gitee_name"], user.gitee_name)
