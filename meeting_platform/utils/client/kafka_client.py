#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/22 20:18
# @Author  : Tom_zc
# @FileName: kafka_client.py
# @Software: PyCharm
import json

from kafka import KafkaProducer


class KafKaClient:
    def __init__(self, server=None):
        if server is None:
            server = ["localhost:9092"]
        self.client = KafkaProducer(
            bootstrap_servers=server,
            value_serializer=lambda v: json.dumps(v).encode()
        )

    def __enter__(self):
        return self

    def send_msg(self, topic, msg):
        self.client.send(topic, msg)
        self.client.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close(timeout=180)
