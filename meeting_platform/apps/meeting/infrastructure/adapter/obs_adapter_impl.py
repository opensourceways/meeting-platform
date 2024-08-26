# -*- coding: utf-8 -*-
# @Time    : 2023/11/22 20:33
# @Author  : Tom_zc
# @FileName: obs_client.py
# @Software: PyCharm
from obs import ObsClient

from meeting.domain.repository.obs_adapter import ObsAdapter

from meeting_platform.utils.client.obs_client import MyObsClient


class ObsAdapterImp(MyObsClient, ObsAdapter):
    pass
