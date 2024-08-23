#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 20:31
# @Author  : Tom_zc
# @FileName: zoom_api.py
# @Software: PyCharm
import datetime
import json
import secrets
import requests
import logging

# noinspection PyPackageRequirements
from obs import ObsClient
from django.conf import settings

from meeting_platform.utils.common import get_video_path
from meeting_platform.utils.file_stream import download_big_file
from meeting.domain.repository.meeting_adapter import MeetingAdapter
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.zoom_action import ZoomCreateAction, \
    ZoomUpdateAction, ZoomDeleteAction, ZoomGetParticipantsAction, ZoomGetVideo

logger = logging.getLogger("log")


class ZoomApi(MeetingAdapter):
    meeting_type = "zoom"  # it is platform

    create_path = "/v2/users/{}/meetings"
    update_path = "/v2/meetings/{}"
    delete_path = "/v2/meetings/{}"
    participants_path = "/v2/past_meetings/{}/participants?page_size=300"
    records_path = "/v2/users/{}/recordings"

    def __init__(self, community, host_id):
        platform_info = settings.VAULT_CONF["COMMUNITY_HOST"][community]
        cur_platform_info = [i for i in platform_info if i["HOST"] == host_id]
        if len(cur_platform_info) == 1:
            self.account = cur_platform_info[0]["ACCOUNT"]
        else:
            raise RuntimeError(
                "[TencentApi] init TencentApi failed, and get config({}) failed.".format(len(cur_platform_info)))
        self.api_prefix = settings.CONF["API_PREFIX"]["ZOOM_API_PREFIX"]
        self.time_out = settings.REQUEST_TIMEOUT
        self.upload_date = settings.UPLOAD_BILIBILI_DATE
        self.video_min_size = settings.VIDEO_MINI_SIZE

    def _get_url(self, uri):
        """get url"""
        return self.api_prefix + uri

    def _get_oauth_token(self):
        """get oauth token"""
        obs_client = ObsClient(access_key_id=settings.ACCESS_KEY_ID_2,
                               secret_access_key=settings.SECRET_ACCESS_KEY_2,
                               server=settings.OBS_ENDPOINT_2)
        res = obs_client.getObjectMetadata(settings.OBS_BUCKET_NAME_2,
                                           settings.ZOOM_TOKEN_OBJECT)
        token = ''
        if res.get('status') != 200:
            logger.error('Fail to get zoom token')
            return token
        for k, v in res.get('header'):
            if k == 'access_token':
                token = v
                break
        logger.info('Get zoom token successfully')
        return token

    def create(self, action):
        """create meeting"""
        if not isinstance(action, ZoomCreateAction):
            raise RuntimeError("action must be the subclass of ZoomCreateAction")
        start_time = (datetime.datetime.strptime(action.date + action.start, '%Y-%m-%d%H:%M') -
                      datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = (datetime.datetime.strptime(action.date + action.end, '%Y-%m-%d%H:%M') -
                    datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:%M:%SZ')
        duration = int((datetime.datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%SZ') -
                        datetime.datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%SZ')).seconds / 60)
        token = self._get_oauth_token()
        headers = {
            "content-type": "application/json",
            "authorization": "Bearer {}".format(token)
        }
        payload = {
            'start_time': start_time,
            'duration': duration,
            'topic': action.topic,
            'password': secrets.token_hex(3),
            'settings': {
                'waiting_room': False,
                'auto_recording': action.is_record,
                'join_before_host': True,
                'jbh_time': 5
            }
        }
        uri = self.create_path.format(action.host_id)
        response = requests.post(self._get_url(uri), data=json.dumps(payload), headers=headers,
                                 timeout=(settings.LINK_TIMEOUT_TIME, settings.READ_TIMEOUT_TIME))
        resp_dict = {}
        if response.status_code != 201:
            return response.status_code, resp_dict
        resp_dict['mid'] = response.json()['id']
        resp_dict['start_url'] = response.json()['start_url']
        resp_dict['join_url'] = response.json()['join_url']
        resp_dict['host_id'] = response.json()['host_id']
        return response.status_code, resp_dict

    def update(self, action):
        """update meeting"""
        if not isinstance(action, ZoomUpdateAction):
            raise RuntimeError("action must be the subclass of ZoomUpdateAction")
        start = action.start
        end = action.end
        date = action.date
        # 计算duration
        if int(start.split(':')[0]) >= 8:
            start_time = date + 'T' + ':'.join([str(int(start.split(':')[0]) - 8), start.split(':')[1], '00Z'])
        else:
            d1 = datetime.datetime.strptime(date, '%Y-%m-%d') - datetime.timedelta(days=1)
            d2 = datetime.datetime.strftime(d1, '%Y-%m-%d %H%M%S')[:10]
            start_time = d2 + 'T' + ':'.join([str(int(start.split(':')[0]) + 16), start.split(':')[1], '00Z'])
        duration = (int(end.split(':')[0]) - int(start.split(':')[0])) * 60 + \
                   (int(end.split(':')[1]) - int(start.split(':')[1]))
        # 准备好调用zoom api的data
        new_data = {'settings': {}, 'start_time': start_time, 'duration': duration, 'topic': action.topic}
        new_data['settings']['waiting_room'] = False
        new_data['settings']['auto_recording'] = action.is_record
        token = self._get_oauth_token()
        headers = {
            "content-type": "application/json",
            "authorization": "Bearer {}".format(token)
        }
        uri = self.update_path.format(action.mid)
        # 发送patch请求，修改会议
        response = requests.patch(self._get_url(uri), data=json.dumps(new_data), headers=headers,
                                  timeout=(settings.LINK_TIMEOUT_TIME, settings.READ_TIMEOUT_TIME))
        return response.status_code

    def delete(self, action):
        """delete meeting"""
        if not isinstance(action, ZoomDeleteAction):
            raise RuntimeError("action must be the subclass of ZoomDeleteAction")
        uri = self.delete_path.format(action.mid)
        token = self._get_oauth_token()
        headers = {
            "authorization": "Bearer {}".format(token)
        }
        response = requests.request("DELETE", self._get_url(uri), headers=headers,
                                    timeout=(settings.LINK_TIMEOUT_TIME, settings.READ_TIMEOUT_TIME))
        return response.status_code

    def get_participants(self, action):
        """get participants from meeting"""
        if not isinstance(action, ZoomGetParticipantsAction):
            raise RuntimeError("action must be the subclass of ZoomGetParticipantsAction")
        uri = self.participants_path.format(action.mid)
        token = self._get_oauth_token()
        headers = {
            "authorization": "Bearer {}".format(token)}
        r = requests.get(self._get_url(uri), headers=headers,
                         timeout=(settings.LINK_TIMEOUT_TIME, settings.READ_TIMEOUT_TIME))
        if r.status_code == 200:
            total_records = r.json()['total_records']
            participants = r.json()['participants']
            resp = {'total_records': total_records, 'participants': [{'name': x['name']} for x in participants]}
            return r.status_code, resp
        else:
            return r.status_code, r.json()

    def get_records(self, action):
        """get all records"""
        mid = action.meeting["mid"]
        host_id = action.meeting["host_id"]
        uri = self.records_path.format(host_id)
        token = self._get_oauth_token()
        headers = {
            'authorization': 'Bearer {}'.format(token)
        }
        params = {
            'from': (datetime.datetime.now() -
                     datetime.timedelta(days=settings.UPLOAD_BILIBILI_DATE)).strftime("%Y-%m-%d"),
            'page_size': 50
        }
        response = requests.get(self._get_url(uri), headers=headers, params=params,
                                timeout=(settings.LINK_TIMEOUT_TIME, settings.READ_TIMEOUT_TIME))
        if response.status_code != 200:
            logger.error('get recordings: {} {}'.format(response.status_code, response.json()['message']))
            return
        if "meetings" not in response.json():
            return
        all_mid = [x['id'] for x in response.json()['meetings']]
        if all_mid.count(int(mid)) == 0:
            logger.info('meeting {}: no recordings yet'.format(mid))
            return
        if all_mid.count(int(mid)) == 1:
            record = list(filter(lambda x: x if x['id'] == int(mid) else None, response.json()['meetings']))[0]
            return record
        if all_mid.count(int(mid)) > 1:
            records = list(filter(lambda x: x if x['id'] == int(mid) else None, response.json()['meetings']))
            max_size = max([x['total_size'] for x in records])
            record = list(filter(lambda x: x if x['total_size'] == max_size else None, response.json()['meetings']))[0]
            return record

    def _get_download_url(self, action, recordings):
        """get download url"""
        mid = action.meeting["mid"]
        if not recordings:
            logger.error("{} find empty records.".format(mid))
            return
        recordings_list = list(
            filter(lambda x: x if x['file_extension'] == 'MP4' else None, recordings['recording_files']))
        if len(recordings_list) == 0:
            logger.info('{}: filtered records and result is empty'.format(mid))
            return
        if len(recordings_list) > 1:
            max_size = max([x['file_size'] for x in recordings_list])
            for recording in recordings_list:
                if recording['file_size'] != max_size:
                    recordings_list.remove(recording)
        total_size = recordings_list[0]['file_size']
        logger.info('meeting {}: the full size of the recording file is {}'.format(mid, total_size))
        if total_size < settings.VIDEO_MINI_SIZE:
            logger.info('meeting {}: the file is too small to upload'.format(mid))
            return
        return recordings_list[0]['download_url']

    def _download_video(self, action, download_url):
        """download video"""
        mid = action.meeting["mid"]
        video_path = get_video_path(mid)
        r = requests.get(url=download_url, allow_redirects=False,
                         timeout=(settings.LINK_TIMEOUT_TIME, settings.READ_TIMEOUT_TIME))
        url = r.headers['location']
        filename = download_big_file(url, video_path)
        return filename

    def get_video(self, action):
        if not isinstance(action, ZoomGetVideo):
            raise RuntimeError("action must be the subclass of ZoomPrepareVideo")
        records = self.get_records(action)
        if not records:
            logger.error("{}: get empty records.".format(action.meeting["mid"]))
            return
        download_url = self._get_download_url(action, records)
        if not download_url:
            logger.error("{}: get empty download_url.".format(action.meeting["mid"]))
            return
        video_path = self._download_video(action, download_url)
        return video_path
