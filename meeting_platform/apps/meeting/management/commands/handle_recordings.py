#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/8/26 11:16
# @Author  : Tom_zc
# @FileName: handle_recordings.py
# @Software: PyCharm
import os
import shutil
import logging
import traceback
from multiprocessing.dummy import Pool as ThreadPool

from django.conf import settings
from django.core.management.base import BaseCommand
from django.forms import model_to_dict

from meeting.infrastructure.adapter.bilibili_adapter_impl import BiliAdapterImpl
from meeting.infrastructure.adapter.meeting_adapter_impl.apis.base_api import handler_meeting
from meeting.infrastructure.adapter.meeting_adapter_impl.meeting_adapter_impl import MeetingAdapterImpl
from meeting.infrastructure.adapter.upload_adapter_impl.bili_upload_adapter_impl import BiliUploadAdapterImpl
from meeting.infrastructure.adapter.upload_adapter_impl.obs_upload_adapter_impl import ObsUploadAdapterImpl
from meeting.infrastructure.dao.meeting_dao import MeetingDao
from meeting_platform.utils.common import execute_cmd3
from meeting_platform.utils.file_stream import write_content

logger = logging.getLogger("log")


class HandleRecording:
    meeting_dao = MeetingDao
    bili_adapter_impl = BiliAdapterImpl
    meeting_adapter_impl = MeetingAdapterImpl()
    upload_adapter_impl = [BiliUploadAdapterImpl, ObsUploadAdapterImpl]

    def __init__(self, community):
        self.community = community

    def check_and_refresh_upload_results(self):
        logger.info(
            '[HandleRecording/check_upload_results] {} Start to check results for uploading videos to bili'.format(
                self.community))
        adapter_impl = self.bili_adapter_impl(self.community)
        all_vid = adapter_impl.search_all_videos()
        empty_replay_url_mid = self.meeting_dao.get_upload_mid_by_community(self.community)
        exist_mid = list(set(empty_replay_url_mid) - set(all_vid))
        logger.info(
            '[HandleRecording/check_upload_results/{}] find uploaded video:{}'.format(
                self.community, ",".join(exist_mid)))
        self.meeting_dao.update_upload_status_by_community_and_mid(self.community, exist_mid)

    # noinspection LongLine
    def _cover_content(self, topic, group_name, date, start_time, end_time):
        content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>cover</title>
        </head>
        <body>
            <div style="display: inline-block; height: 688px; width: 1024px; text-align: center; background-image: url('cover.png')">
                <p style="font-size: 100px;margin-top: 150px; color: white"><b>{0}</b></p>
                <p style="font-size: 80px; margin: 0; color: white">SIG: {1}</p>
                <p style="font-size: 60px; margin: 0; color: white">Time: {2} {3}-{4}</p>
            </div>
        </body>
        </html>
        """.format(topic, group_name, date, start_time, end_time)
        return content

    def _get_video_path(self, meeting):
        """get video path in local file system"""
        action = self.meeting_adapter_impl.get_video_action(meeting["platform"], meeting)
        video_path = handler_meeting(meeting["community"], meeting["platform"], meeting["host_id"], action)
        if not video_path:
            logger.error('[HandleRecording/_get_video_path] meeting {}: video path could not be empty'.
                         format(meeting["mid"]))
            return
        if not os.path.exists(video_path):
            logger.error('[HandleRecording/_get_video_path] meeting {}: video path could not be exist'.
                         format(meeting["mid"]))
            return
        if os.path.getsize(video_path) == 0:
            logger.error('[HandleRecording/_get_video_path] meeting {}: download but did not get the full video'.
                         format(meeting["mid"]))
            return
        return video_path

    def _get_video_cover_path(self, video_path, meeting):
        # 1. generate cover image
        cover_path = self._generate_cover(meeting, video_path)
        if not os.path.exists(cover_path):
            logger.error('meeting {}: fail to generate cover for meeting video'.format(meeting["mid"]))
            return
        return cover_path

    def _generate_cover(self, meeting, filename):
        html_path = filename.replace('.mp4', '.html')
        image_path = filename.replace('.mp4', '.png')
        mid = meeting["mid"]
        topic = meeting["topic"]
        group_name = meeting["group_name"]
        date = meeting["date"]
        start = meeting["start"]
        end = meeting["end"]
        community = meeting["community"]
        content = self._cover_content(topic, group_name, date, start, end)
        write_content(html_path, content, model="w")
        if not os.path.exists(os.path.join(os.path.dirname(filename), 'cover.png')):
            shutil.copy("meeting_platform/templates/image/{}/cover.png".format(community), os.path.dirname(filename))
        execute_cmd3("wkhtmltoimage --enable-local-file-access {} {}".format(html_path, image_path))
        logger.info("[HandleRecording/_generate_cover] meeting {}: generate cover success".format(mid))
        return image_path

    def upload(self):
        meeting_infos = self.meeting_dao.get_un_upload_all_by_community(self.community)
        for meeting in meeting_infos:
            meeting = model_to_dict(meeting)
            video_path = self._get_video_path(meeting)
            if not video_path:
                continue
            cover_path = self._get_video_cover_path(video_path, meeting)
            if not cover_path:
                continue
            for handler in self.upload_adapter_impl:
                try:
                    ret = handler(meeting).upload(video_path, cover_path)
                    if not ret:
                        raise Exception("[HandleRecording/upload] meeting mid:{}".format(meeting["mid"]))
                except Exception as e:
                    logger.error("[HandleRecording/upload] e:{}, traceback:{}".format(str(e), traceback.format_exc()))
                    break


def work_flow(handle_recording: HandleRecording):
    """按照社区进行分类操作
        1.先将之前上传B站的数据状态更新
        2.下载本地再上传到OBS, 再上传bilibili
    :param handle_recording:
    :return:
    """
    handle_recording.check_and_refresh_upload_results()
    handle_recording.upload()
    return True


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info('-' * 20 + ' start to handler recordings' + '-' * 20)
        logger.info('[handle] find community: {}'.format(",".join(settings.COMMUNITY_SUPPORT)))
        handler_recording_communities = [HandleRecording(i) for i in settings.COMMUNITY_SUPPORT]
        pool = ThreadPool()
        pool.map(work_flow, handler_recording_communities)
        pool.close()
        pool.join()
        logger.info('-' * 20 + 'All done' + '-' * 20)
