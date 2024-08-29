#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/7/9 20:30
# @Author  : Tom_zc
# @FileName: wk_api.py
# @Software: PyCharm
import datetime
import json
import logging
import os
import requests
import time

from django.conf import settings

from meeting_platform.utils.common import get_video_path
from meeting_platform.utils.file_stream import download_big_file
from meeting.domain.repository.meeting_adapter import MeetingAdapter
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.wk_action import WkCreateAction, WkUpdateAction, \
    WkDeleteAction, WkGetParticipantsAction, WkGetVideo

logger = logging.getLogger('log')


# noinspection SpellCheckingInspection
class WkApi(MeetingAdapter):
    meeting_type = "welink"  # it is platform

    proxy_token_path = "/v1/usg/acs/auth/proxy"
    create_path = "/v1/mmc/management/conferences"
    update_path = "/v1/mmc/management/conferences"
    delete_path = "/v1/mmc/management/conferences"
    participants_path = "/v1/mmc/management/conferences/history/confAttendeeRecord"
    list_history_path = "/v1/mmc/management/conferences/history"
    download_url_path = "/v1/mmc/management/record/downloadurls"
    list_recordings_path = "/v1/mmc/management/record/files"

    def __init__(self, community, platform, host_id):
        platform_info = settings.COMMUNITY_HOST[community][platform]
        cur_platforms = [i for i in platform_info if i["HOST"] == host_id]
        if len(cur_platforms) == 1:
            cur_platform_info = cur_platforms[0]
        else:
            raise RuntimeError(
                "[WkApi] init WkApi failed, and get config({}) failed.".format(len(cur_platforms)))
        self.account = cur_platform_info["ACCOUNT"]
        self.pwd = cur_platform_info["PWD"]
        self.api_prefix = settings.API_PREFIX["WELINK_API_PREFIX"]
        self.host_id = host_id
        self.community = community
        self.platform = platform
        self.time_out = settings.REQUEST_TIMEOUT
        self.bili_upload_date = settings.BILI_UPLOAD_DATE
        self.bili_video_min_size = settings.BILI_VIDEO_MIN_SIZE

    def _get_url(self, uri):
        return self.api_prefix + uri

    def _create_proxy_token(self):
        """获取代理鉴权token"""
        headers = {
            'Content-Type': 'application/json; charset=UTF-8'
        }
        payload = {
            'authServerType': 'workplace',
            'authType': 'AccountAndPwd',
            'clientType': 72,
            'account': self.account,
            'pwd': self.pwd
        }
        response = requests.post(self._get_url(self.proxy_token_path), headers=headers, data=json.dumps(payload),
                                 timeout=self.time_out)
        if response.status_code != 200:
            logger.error('[WkApi] Fail to get proxy token, status_code: {}'.format(response.status_code))
            return None
        return response.json()['accessToken']

    def create(self, action):
        """创建会议"""
        if not isinstance(action, WkCreateAction):
            raise RuntimeError("[WkApi] action must be the subclass of WkCreateAction")
        access_token = self._create_proxy_token()
        start_time = (datetime.datetime.strptime(action.date + action.start, '%Y-%m-%d%H:%M') -
                      datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        duration_time = int((datetime.datetime.strptime(action.end, '%H:%M') -
                             datetime.datetime.strptime(action.start, '%H:%M')).seconds / 60)
        headers = {
            'Content-Type': 'application/json',
            'X-Access-Token': access_token
        }
        data = {
            'startTime': start_time,
            'length': duration_time,
            'subject': action.topic,
            'mediaTypes': 'HDVideo',
            'confConfigInfo': {
                'isAutoMute': True,
                'isHardTerminalAutoMute': True,
                'isGuestFreePwd': True,
                'allowGuestStartConf': True,
                'vmrIDType': 1,
                'prolongLength': 15,
                'enableWaitingRoom': False
            },
            'vmrFlag': 1,
            'vmrID': self.host_id
        }
        if action.is_record:
            data['isAutoRecord'] = 1
            data['recordType'] = 2
        response = requests.post(self._get_url(self.create_path), headers=headers, data=json.dumps(data),
                                 timeout=self.time_out)
        resp_dict = {}
        if response.status_code != 200:
            logger.error('[WkApi] Fail to create meeting, status_code is {}'.format(response.status_code))
            return response.status_code, resp_dict
        resp_dict['mid'] = response.json()[0]['conferenceID']
        resp_dict['start_url'] = response.json()[0]['chairJoinUri']
        resp_dict['join_url'] = response.json()[0]['guestJoinUri']
        resp_dict['host_id'] = self.host_id
        return response.status_code, resp_dict

    def update(self, action):
        if not isinstance(action, WkUpdateAction):
            raise RuntimeError("[WkApi] action must be the subclass of WkUpdateAction")
        access_token = self._create_proxy_token()
        start_time = (datetime.datetime.strptime(action.date + action.start, '%Y-%m-%d%H:%M') -
                      datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
        length = int((datetime.datetime.strptime(action.end, '%H:%M') -
                      datetime.datetime.strptime(action.start, '%H:%M')).seconds / 60)
        headers = {
            'Content-Type': 'application/json',
            'X-Access-Token': access_token
        }
        data = {
            'startTime': start_time,
            'length': length,
            'subject': action.topic,
            'mediaTypes': 'HDVideo',
            'confConfigInfo': {
                'isAutoMute': True,
                'isHardTerminalAutoMute': True,
                'isGuestFreePwd': True,
                'allowGuestStartConf': True
            }
        }
        params = {'conferenceID': action.mid}
        if action.is_record:
            data['isAutoRecord'] = 1
            data['recordType'] = 2
        else:
            data['isAutoRecord'] = 0
            data['recordType'] = 0
        response = requests.put(self._get_url(self.update_path), params=params, headers=headers, data=json.dumps(data),
                                timeout=self.time_out)
        return response.status_code

    def delete(self, action):
        """删除会议"""
        if not isinstance(action, WkDeleteAction):
            raise RuntimeError("[WkApi] action must be the subclass of WkDeleteAction")
        access_token = self._create_proxy_token()
        headers = {
            'X-Access-Token': access_token
        }
        params = {
            'conferenceID': action.mid,
            'type': 1
        }
        response = requests.delete(self._get_url(self.delete_path), headers=headers, params=params,
                                   timeout=self.time_out)
        if response.status_code != 200:
            logger.error('[WkApi] Fail to cancel meeting {}, and return data:{}'.format(action.mid, response.json()))
            return response.status_code
        logger.info('[WkApi] Cancel meeting {}'.format(action.mid))
        return response.status_code

    def _list_history_meeting(self, action):
        """获取历史会议列表"""
        access_token = self._create_proxy_token()
        start_time = ' '.join([action.date, action.start])
        end_time = ' '.join([action.date, action.end])
        start_date = int(time.mktime((datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M') -
                                      datetime.timedelta(days=7)).timetuple())) * 1000
        end_date = int(time.mktime((datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M') +
                                    datetime.timedelta(days=7)).timetuple())) * 1000
        headers = {
            'X-Access-Token': access_token
        }
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'limit': 500
        }
        response = requests.get(self._get_url(self.list_history_path), headers=headers, params=params,
                                timeout=self.time_out)
        if response.status_code != 200:
            logger.error('[WkApi] Fail to get history meetings list')
            logger.error(response.json())
            return {}
        return response.json()

    def get_participants(self, action):
        """获取参会人员"""
        if not isinstance(action, WkGetParticipantsAction):
            raise RuntimeError("[WkApi] action must be the subclass of WkGetParticipantsAction")
        access_token = self._create_proxy_token()
        if not access_token:
            return 401, {'message': 'UnAuthorized'}
        headers = {
            'X-Access-Token': access_token
        }
        meetings_lst = self._list_history_meeting(action)
        meetings_data = meetings_lst.get('data')
        participants = {
            'total_records': 0,
            'participants': []
        }
        status = 200
        for item in meetings_data:
            if item['conferenceID'] == str(action.mid):
                conf_uuid = item['confUUID']
                params = {
                    'confUUID': conf_uuid,
                    'limit': 500
                }
                response = requests.get(self._get_url(self.participants_path), headers=headers, params=params,
                                        timeout=self.time_out)
                if response.status_code == 200:
                    participants['total_records'] += response.json()['count']
                    for participant_info in response.json()['data']:
                        participants['participants'].append({'name': participant_info['displayName']})
                else:
                    status = response.status_code
                    participants = response.json()
                    break
        return status, participants

    def _list_recordings(self):
        """获取录像列表"""
        access_token = self._create_proxy_token()
        tn = int(time.time())
        headers = {
            'X-Access-Token': access_token
        }
        params = {
            'startDate': tn * 1000,
            'endDate': (tn - self.bili_upload_date * 3600 * 24) * 1000,
            'limit': 100
        }
        response = requests.get(self._get_url(self.list_recordings_path), headers=headers, params=params,
                                timeout=self.time_out)
        return response.status_code, response.json()

    def _get_download_url(self, conf_uuid):
        """获取录像下载地址"""
        headers = {
            'X-Access-Token': self._create_proxy_token()
        }
        params = {
            'confUUID': conf_uuid
        }
        response = requests.get(self._get_url(self.download_url_path), headers=headers, params=params,
                                timeout=self.time_out)
        return response.status_code, response.json()

    def _download_recording(self, token, target_filename, download_url):
        """下载云录制的视频"""
        if os.path.exists(target_filename):
            os.remove(target_filename)
        headers = {"Authorization": token}
        download_big_file(download_url, target_filename, headers=headers)

    # noinspection PyPep8Naming
    def _get_records(self, action):
        """get the records"""
        mid = action.mid
        date = action.date
        start = action.start
        end = action.end
        start_time = date + ' ' + start
        end_time = date + ' ' + end
        status, recordings = self._list_recordings()
        if status != 200:
            logger.error('[WkApi/_get_records] {}/{}:Fail to get welink recordings, and return is:{}.'.
                         format(self.community, mid, status))
            return []
        if recordings['count'] == 0:
            logger.error('[WkApi/_get_records] {}/{}:get empty welink recordings.'
                         .format(self.community, mid))
            return []
        available_recordings = []
        start_order_set = set()
        recordings_data = recordings['data']
        for recording in recordings_data:
            if recording['confID'] != mid:
                continue
            startTime = (datetime.datetime.strptime(recording['startTime'], '%Y-%m-%d %H:%M') +
                         datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
            rcdTime = recording['rcdTime']
            endTime = (datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M') +
                       datetime.timedelta(seconds=rcdTime)).strftime('%Y-%m-%d %H:%M')
            if endTime < start_time or startTime > end_time:
                continue
            start_order_set.add(startTime)
        for st in sorted(list(start_order_set)):
            for recording in recordings_data:
                if recording['confID'] != mid:
                    continue
                startTime = (datetime.datetime.strptime(recording['startTime'], '%Y-%m-%d %H:%M') +
                             datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')
                rcdTime = recording['rcdTime']
                endTime = (datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M') +
                           datetime.timedelta(seconds=rcdTime)).strftime('%Y-%m-%d %H:%M')
                if endTime < start_time or startTime > end_time:
                    continue
                if startTime == st:
                    available_recordings.append(recording)
        return available_recordings

    def _download_video(self, action, recordings):
        """download video"""
        mid = action.mid
        waiting_download_recordings = []
        for available_recording in recordings:
            conf_uuid = available_recording['confUUID']
            status, res = self._get_download_url(conf_uuid)
            if status != 200:
                logger.error('[WkApi/_download_video] {}/{}:Fail to get welink recordings, and return is:{}.'.
                             format(self.community, mid, status))
                continue
            record_urls = res['recordUrls'][0]['urls']
            for record_url in record_urls:
                if record_url['fileType'].lower() in ['hd', 'aux']:
                    waiting_download_recordings.append(record_url)
        if not waiting_download_recordings:
            logger.info('[WkApi/_download_video] {}/{} filter to no available recordings'.
                        format(self.community, mid))
            return
        token = waiting_download_recordings[-1]['token']
        download_url = waiting_download_recordings[-1]['url']
        target_filename = get_video_path(mid, self.community)
        self._download_recording(token, target_filename, download_url)
        return target_filename

    def get_video(self, action):
        """download video to local"""
        if not isinstance(action, WkGetVideo):
            raise RuntimeError("[WkApi/get_video] action must be the subclass of WkGetVideo")
        recordings = self._get_records(action)
        if not recordings:
            logger.info('[WkApi/get_video] {} filter to no available recordings which mid is：{}'
                        .format(self.community, action.mid))
            return
        return self._download_video(action, recordings)
