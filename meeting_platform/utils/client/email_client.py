#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/22 19:40
# @Author  : Tom_zc
# @FileName: email_client.py
# @Software: PyCharm

import smtplib
import traceback
from logging import getLogger

from django.conf import settings

logger = getLogger("log")


class EmailClient(object):
    """EmailClient"""

    def __init__(self, community):
        """init smtp client"""
        self.community = community
        self.smtp_info = settings.COMMUNITY_SMTP[community]
        self.server = smtplib.SMTP(self.smtp_info["SMTP_SERVER_HOST"], self.smtp_info["SMTP_SERVER_PORT"])
        self.server.ehlo()
        self.server.starttls()
        self.server.login(self.smtp_info["SMTP_SERVER_USER"], self.smtp_info["SMTP_SERVER_PASS"])

    def send_message(self, receive_str, msg, is_close=True):
        """send the message by email client"""
        try:
            msg['From'] = '{} conference <{}>'.format(self.community, self.smtp_info["SMTP_MESSAGE_FROM"])
            return self.server.sendmail(self.smtp_info["SMTP_MESSAGE_FROM"], receive_str, msg)
        except smtplib.SMTPException as e:
            logger.error("[EmailClient] e:{},traceback:{}".format(e, traceback.format_exc()))
        finally:
            if is_close:
                self.server.quit()
