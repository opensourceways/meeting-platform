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

    def __init__(self, host, port, user, pwd):
        """init smtp client"""
        self.server = smtplib.SMTP(host, port)
        self.server.ehlo()
        self.server.starttls()
        self.server.login(user, pwd)

    def send_message(self, from_str, receive_str, msg, is_close=True):
        """send the message by email client"""
        try:
            return self.server.sendmail(from_str, receive_str, msg.as_string())
        except smtplib.SMTPException as e:
            logger.error("[EmailClient] e:{},traceback:{}".format(e, traceback.format_exc()))
        finally:
            if is_close:
                self.server.quit()
