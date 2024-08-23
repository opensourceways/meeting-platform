#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/11 12:18
# @Author  : Tom_zc
# @FileName: bilibili_client.py
# @Software: PyCharm
from django.conf import settings

from bilibili_api import Credential, video_uploader, sync
from bilibili_api.user import User

from meeting.domain.repository.bilibili_adapter import BiliAdapter


class BiliAdapterImpl(BiliAdapter):
    def __init__(self, sess_data=None, jct_data=None):
        """init bilibili credential"""
        sess_data = sess_data if sess_data else settings.SESS_DATA
        jct_data = jct_data if jct_data else settings.BILI_JCT
        self.credential = Credential(sessdata=sess_data, bili_jct=jct_data)

    def upload(self, meeting_info, video_path, thumbnail_path):
        tag = meeting_info.get('tag')
        title = meeting_info.get('title')
        desc = meeting_info.get('desc')
        page = video_uploader.VideoUploaderPage(path=video_path, title=title, description=desc)
        meta = {
            'copyright': 1,
            'desc': desc,
            'desc_format_id': 0,
            'dynamic': '',
            'interactive': 0,
            'no_reprint': 1,
            'subtitles': {
                'lan': '',
                'open': 0
            },
            'tag': tag,
            'tid': 124,
            'title': title
        }
        uploader = video_uploader.VideoUploader([page], meta, self.credential, cover=thumbnail_path)
        res = sync(uploader.start())
        return res

    def search_all_videos(self):
        user = User(settings.BILI_UID, self.credential)
        all_vid = []
        pn = 1
        while True:
            res = sync(user.get_videos(pn=pn))
            if len(res.get('list').get('vlist')) == 0:
                break
            for video in res['list']['vlist']:
                b_vid = video.get('bvid')
                if not b_vid:
                    continue
                if b_vid not in all_vid:
                    all_vid.append(b_vid)
            pn += 1
        return all_vid

    def get_replay_url(self, b_vid):
        return settings.BILI_VIDEO_PREFIX + b_vid
