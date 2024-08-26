#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/6/19 16:36
# @Author  : Tom_zc
# @FileName: tencent_api.py
# @Software: PyCharm
import base64
import hashlib
import hmac
import json
import logging
import requests
import time
from datetime import datetime

from django.conf import settings

from meeting_platform.utils.common import make_nonce, get_video_path
from meeting_platform.utils.file_stream import download_big_file
from meeting.domain.repository.meeting_adapter import MeetingAdapter
from meeting.infrastructure.adapter.meeting_adapter_impl.actions.tencent_action import TencentCreateAction, \
    TencentDeleteAction, TencentGetParticipantsAction, TencentGetVideo, TencentUpdateAction

logger = logging.getLogger('log')


class TencentApi(MeetingAdapter):
    meeting_type = "tencent"  # it is platform

    create_path = "/v1/meetings"
    update_path = "/v1/meetings/{}"
    delete_path = "/v1/meetings/{}/cancel"
    participants_path = "/v1/meetings/{}/participants?userid={}"
    record_path = "/v1/corp/records?start_time={}&end_time={}&page_size=20&page={}"
    video_download_path = "/v1/addresses/{}?userid={}"

    def __init__(self, community, platform, host_id):
        platform_info = settings.COMMUNITY_HOST[community][platform]
        cur_platform_info = [i for i in platform_info if i["HOST"] == host_id]
        if len(cur_platform_info) == 1:
            self.app_id = cur_platform_info[0]["TENCENT_APP_ID"]
            self.sdk_id = cur_platform_info[0]["TENCENT_SDK_ID"]
            self.secret_id = cur_platform_info[0]["TENCENT_SECRET_ID"]
            self.secret_key = cur_platform_info[0]["TENCENT_SECRET_KEY"]
            self.host_key = cur_platform_info[0]["TENCENT_HOST_KEY"]
            self.host_id = host_id
        else:
            raise RuntimeError(
                "[TencentApi] init TencentApi failed, and get config({}) failed.".format(len(cur_platform_info)))
        self.api_prefix = settings.API_PREFIX["TENCENT_API_PREFIX"]
        self.time_out = settings.REQUEST_TIMEOUT
        self.upload_date = settings.UPLOAD_BILIBILI_DATE
        self.video_min_size = settings.VIDEO_MINI_SIZE

    def _get_url(self, uri):
        """request url"""
        return self.api_prefix + uri

    def _get_time(self, time_temp):
        """get time"""
        return str(int(time.mktime(time.strptime(time_temp, '%Y-%m-%d %H:%M'))))

    def _get_signature(self, method, uri, body):
        """get signature"""
        timestamp = str(int(time.time()))
        nonce = make_nonce()
        headers = {
            "X-TC-Key": self.secret_id,
            "X-TC-Nonce": nonce,
            "X-TC-Timestamp": timestamp,
            "X-TC-Signature": "",
            "AppId": self.app_id,
            "SdkId": self.sdk_id,
            "X-TC-Registered": "1"
        }
        header = 'X-TC-Key=' + self.secret_id + '&X-TC-Nonce=' + nonce + '&X-TC-Timestamp=' + timestamp
        msg = (method + '\n' + header + '\n' + uri + '\n' + body).encode('utf-8')
        key = self.secret_key.encode('utf-8')
        signature = base64.b64encode(hmac.new(key, msg, digestmod=hashlib.sha256).hexdigest().encode()).decode('utf-8')
        headers['X-TC-Signature'] = signature
        return signature, headers

    def create(self, action):
        """create meeting"""
        if not isinstance(action, TencentCreateAction):
            raise RuntimeError("[TencentApi] action must be the subclass of TencentCreateAction")
        date = action.date
        start_time = date + ' ' + action.start
        end_time = date + ' ' + action.end
        start_time = self._get_time(start_time)
        end_time = self._get_time(end_time)
        payload = {
            "userid": self.host_id,
            "instanceid": 1,
            "subject": action.topic,
            "type": 0,
            "start_time": start_time,
            "end_time": end_time,
            "settings": {
                "mute_enable_join": True
            },
            "enable_host_key": True,
            "host_key": self.host_key
        }
        if action.is_record:
            payload['settings']['auto_record_type'] = 'cloud'
            payload['settings']['participant_join_auto_record'] = True
            payload['settings']['enable_host_pause_auto_record'] = True
        uri = self.create_path
        url = self._get_url(uri)
        signature, headers = self._get_signature('POST', uri, json.dumps(payload))
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.time_out)
        resp_dict = {
            'host_id': self.host_id
        }
        if r.status_code != 200:
            logger.error('[TencentApi] Fail to create meeting, status_code is {}'.format(r.status_code))
            return r.status_code, resp_dict
        ret_json = r.json()
        resp_dict['mid'] = ret_json['meeting_info_list'][0]['meeting_code']
        resp_dict['mmid'] = ret_json['meeting_info_list'][0]['meeting_id']
        resp_dict['join_url'] = ret_json['meeting_info_list'][0]['join_url']
        return r.status_code, resp_dict

    def update(self, action):
        if not isinstance(action, TencentUpdateAction):
            raise RuntimeError("[TencentApi] action must be the subclass of TencentUpdateAction")
        date = action.date
        start_time = date + ' ' + action.start
        end_time = date + ' ' + action.end
        start_time = self._get_time(start_time)
        end_time = self._get_time(end_time)
        payload = {
            "userid": self.host_id,
            "instanceid": 1,
            "subject": action.topic,
            "type": 0,
            "start_time": start_time,
            "end_time": end_time,
            "settings": {
                "mute_enable_join": True
            },
            "enable_host_key": True,
            "host_key": self.host_key
        }
        if action.is_record:
            payload['settings']['auto_record_type'] = 'cloud'
            payload['settings']['participant_join_auto_record'] = True
            payload['settings']['enable_host_pause_auto_record'] = True
        else:
            payload['settings']['auto_record_type'] = 'none'
        uri = self.update_path.format(action.mmid)
        url = self._get_url(uri)
        signature, headers = self._get_signature('PUT', uri, json.dumps(payload))
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=self.time_out)
        resp_dict = {
            'host_id': self.host_id
        }
        if r.status_code != 200:
            logger.error('[TencentApi] Fail to create meeting, status_code is {}'.format(r.status_code))
            return r.status_code, resp_dict
        ret_json = r.json()
        resp_dict['mid'] = ret_json['meeting_info_list'][0]['meeting_code']
        resp_dict['mmid'] = ret_json['meeting_info_list'][0]['meeting_id']
        resp_dict['join_url'] = ret_json['meeting_info_list'][0]['join_url']
        return r.status_code, resp_dict

    def delete(self, action):
        if not isinstance(action, TencentDeleteAction):
            raise RuntimeError("[TencentApi] action must be the subclass of TencentDeleteAction")
        payload = json.dumps({
            "userid": self.host_id,
            "instanceid": 1,
            "reason_code": 1
        })
        mid = action.mid
        uri = self.delete_path.format(action.mmid)
        url = self._get_url(uri)
        signature, headers = self._get_signature('POST', uri, payload)
        r = requests.post(url, headers=headers, data=payload,
                          timeout=self.time_out)
        if r.status_code != 200:
            logger.error('Fail to cancel meeting {}'.format(mid))
            logger.error(r.json())
            return r.status_code
        logger.info('[TencentApi] Cancel meeting {}'.format(mid))
        return r.status_code

    def get_participants(self, action):
        if not isinstance(action, TencentGetParticipantsAction):
            raise RuntimeError("[TencentApi] action must be the subclass of TencentGetParticipantsAction")
        mmid = action.mmid
        uri = self.participants_path.format(mmid, self.host_id)
        url = self._get_url(uri)
        signature, headers = self._get_signature('GET', uri, "")
        r = requests.get(url, headers=headers, timeout=self.time_out)
        if r.status_code == 200:
            res = {
                'total_records': r.json()['total_count'],
                'participants': [{'name': base64.b64decode(x['user_name'].encode()).decode()} for x in
                                 r.json()['participants']]
            }
            return r.status_code, res
        return r.status_code, r.json()

    def _get_records(self):
        """get records"""
        end_time = int(time.time())
        start_time = end_time - 3600 * 24 * self.upload_date
        page = 1
        records = []
        while True:
            uri = self.record_path.format(start_time, end_time, page)
            signature, headers = self._get_signature('GET', uri, "")
            r = requests.get(self._get_url(uri), headers=headers, timeout=self.time_out)
            if r.status_code != 200:
                logger.error(r.json())
                return []
            if 'record_meetings' not in r.json().keys():
                break
            record_meetings = r.json().get('record_meetings')
            records.extend(record_meetings)
            page += 1
        return records

    def _filter_records(self, action, recordings):
        """filter the avaliable record"""
        mid = action.mid
        if not recordings:
            logger.error("[TencentApi] {}: no available recordings".format(mid))
            return
        match_record = dict()
        mmid = action.mmid
        date = action.date
        start = action.start
        start_time = ' '.join([date, start])
        start_timestamp = int(datetime.timestamp(datetime.strptime(start_time, '%Y-%m-%d %H:%M')))
        for record in recordings:
            if record.get('meeting_id') != mmid:
                continue
            if record.get('state') != 3:
                continue
            media_start_time = record.get('media_start_time')
            if abs(media_start_time // 1000 - start_timestamp) > 1800:
                continue
            record_file = record.get('record_files')[0]
            if record_file.get('record_size') < self.video_min_size:
                logger.error("{}:find the record size lt 10M".format(mid))
                continue
            if not match_record:
                match_record['record_file_id'] = record_file.get('record_file_id')
                match_record['record_size'] = record_file.get('record_size')
                match_record['userid'] = record.get('userid')
            elif record_file.get('record_size') > match_record.get('record_size'):
                match_record['record_file_id'] = record_file.get('record_file_id')
                match_record['record_size'] = record_file.get('record_size')
                match_record['userid'] = record.get('userid')
        if not match_record:
            logger.error('[TencentApi]Find no recordings about Tencent meeting:{}'.format(mid))
            return
        return match_record

    def _get_video_download(self, record_file_id, userid):
        """get video downlaod url"""
        uri = self.video_download_path.format(record_file_id, userid)
        signature, headers = self._get_signature('GET', uri, "")
        r = requests.get(self._get_url(uri), headers=headers, timeout=self.time_out)
        if r.status_code == 200:
            return r.json()['download_address']
        else:
            logger.error(r.text)
            return

    def _download_video(self, action, avaliable_record):
        """download the video"""
        mid = action.mid
        download_url = self._get_video_download(avaliable_record.get('record_file_id'), avaliable_record.get('userid'))
        if not download_url:
            logger.error("[TencentApi] get empty download url:{}".format(mid))
            return
        target_filename = get_video_path(mid)
        download_big_file(download_url, target_filename)
        return target_filename

    def get_video(self, action):
        if not isinstance(action, TencentGetVideo):
            raise RuntimeError("[TencentApi] action must be the subclass of TencentPrepareVideo")
        recordings = self._get_records()
        avaliable_record = self._filter_records(action, recordings)
        if not avaliable_record:
            logger.info('[TencentApi] filter to no available recordings:{}'.format(action.mid))
            return
        return self._download_video(action, avaliable_record)
