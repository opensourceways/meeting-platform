#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/15 10:53
# @Author  : Tom_zc
# @FileName: kafka_client.py
# @Software: PyCharm

import logging
from abc import ABC

from django.conf import settings

from meeting_platform.utils.client.kafka_client import KafKaClient
from meeting_platform.utils.common import func_retry
from meeting.domain.repository.message_adapter import MessageAdapter

logger = logging.getLogger("log")


class MessageKafKaAdapterImpl(MessageAdapter, ABC):
    def get_client(self, meeting):
        kafka_info = settings.COMMUNITY_KAFKA.get(meeting["community"])
        if kafka_info is None:
            return None, None
        else:
            return kafka_info.get("KAFKA_TOPIC"), kafka_info.get("KAFKA_CLIENT")


class CreateMessageKafKaAdapterImpl(MessageKafKaAdapterImpl):

    @func_retry()
    def send_message(self, meeting):
        kafka_topic, kafka_client = self.get_client(meeting)
        if not kafka_topic or not kafka_client:
            logger.info("[CreateMessageAdapterImpl] kafka config is empty, Please ignore.")
            return
        with KafKaClient(settings.KAFKA_CLIENT) as client:
            data = {
                "action": "create_meeting",
                "msg": meeting
            }
            client.send_msg(settings.KAFKA_TOPIC, data)
            logger.info("[CreateMessageAdapterImpl] send create kafka msg success")


class UpdateMessageKafKaAdapterImpl(MessageKafKaAdapterImpl):

    @func_retry()
    def send_message(self, meeting):
        kafka_topic, kafka_client = self.get_client(meeting)
        if not kafka_topic or not kafka_client:
            logger.info("[UpdateMessageKafKaAdapterImpl] kafka config is empty, Please ignore.")
            return
        with KafKaClient(settings.KAFKA_CLIENT) as client:
            data = {
                "action": "update_meeting",
                "msg": meeting
            }
            client.send_msg(settings.KAFKA_TOPIC, data)
            logger.info("[UpdateMessageKafKaAdapterImpl] send update kafka msg success")


class DeleteMessageKafKaAdapterImpl(MessageKafKaAdapterImpl):

    @func_retry()
    def send_message(self, meeting):
        kafka_topic, kafka_client = self.get_client(meeting)
        if not kafka_topic or not kafka_client:
            logger.info("[DeleteMessageKafKaAdapterImpl] kafka config is empty, Please ignore.")
            return
        with KafKaClient(settings.KAFKA_CLIENT) as client:
            data = {
                "action": "delete_meeting",
                "msg": meeting
            }
            client.send_msg(settings.KAFKA_TOPIC, data)
            logger.info("[DeleteMessageAdapterImpl] send delete kafka msg success")
