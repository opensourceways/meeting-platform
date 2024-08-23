import datetime
import logging
import os
import stat

from django.apps import apps as django_apps
from django.db.models import Q
from django.conf import settings

from meeting_platform.utils.client.bilibili_client import BiliClient
from meeting_platform.utils.common import execute_cmd3
from meeting_platform.utils.client.obs_client import ObsClientImp
from meeting_platform.utils.meeting_apis.apis.base_api import handler_meeting
from meeting_platform.utils.meeting_apis.libs import MeetingLib

logger = logging.getLogger('log')
Meeting = django_apps.get_model(settings.MEETING_MODEL)
Video = django_apps.get_model(settings.VIDEO_MODEL)
Record = django_apps.get_model(settings.RECORD_MODEL)


# noinspection LongLine
def cover_content(topic, group_name, date, start_time, end_time):
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


def search_target_meeting_ids():
    past_meetings = Meeting.objects.filter(is_delete=0).filter(
        Q(date__gt=str(datetime.datetime.now() - datetime.timedelta(days=settings.UPLOAD_BILIBILI_DATE))) &
        Q(date__lte=datetime.datetime.now().strftime('%Y-%m-%d'))).values_list('mid', flat=True)
    return [x for x in past_meetings if x in list(Video.objects.filter(replay_url__isnull=True).values_list(
        'mid', flat=True))]


def is_archived(obs_server, bucket_name, object_key):
    search_res = obs_server.getObject(bucket_name, object_key)
    if not isinstance(search_res, dict):
        return False
    if search_res.get('status') != 200:
        return False
    return True


# noinspection SpellCheckingInspection
def generate_cover(meeting, filename):
    html_path = filename.replace('.mp4', '.html')
    image_path = filename.replace('.mp4', '.png')
    mid = meeting.mid
    topic = meeting.topic
    group_name = meeting.group_name
    date = meeting.date
    start = meeting.start
    end = meeting.end
    community = meeting.community
    content = cover_content(topic, group_name, date, start, end)
    flags = os.O_CREAT | os.O_WRONLY
    modes = stat.S_IWUSR | stat.S_IRUSR
    with os.fdopen(os.open(html_path, flags, modes), 'w') as f:
        f.write(content)
    if not os.path.exists(os.path.join(os.path.dirname(filename), 'cover.png')):
        execute_cmd3(
            "cp app_meeting_server/templates/images/{}/cover.png {}".format(community, os.path.dirname(filename)))
    execute_cmd3("wkhtmltoimage --enable-local-file-access {} {}".format(html_path, image_path))
    logger.info("{}: generate cover success".format(mid))
    return image_path


def get_obs_video_object(mid):
    if not Video.objects.filter(mid=mid):
        return
    meeting = Meeting.objects.get(mid=mid)
    date = meeting.date
    group_name = meeting.group_name
    community = meeting.community
    month = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%b').lower()
    return '{0}/{1}/{2}/{3}/{3}.mp4'.format(community, group_name, month, mid)


def get_obs_cover_object(video_object):
    return video_object.replace('.mp4', '.png')


def get_obs_video_download_url(bucket_name, obs_endpoint, video_object):
    return 'https://{}.{}/{}??response-content-disposition=attachment'.format(bucket_name, obs_endpoint, video_object)


def get_size_of_file(file_path):
    if not os.path.exists(file_path):
        logger.error('Could not get size of a non exist file: {}'.format(file_path))
        return
    return os.path.getsize(file_path)


def generate_video_metadata(mid, video_object, video_path):
    meeting = Meeting.objects.get(mid=mid)
    date = meeting.date
    start = meeting.start
    end = meeting.end
    start_time = date + 'T' + start + ':00Z'
    end_time = date + 'T' + end + ':00Z'
    download_url = get_obs_video_download_url(settings.OBS_BUCKETNAME, settings.OBS_ENDPOINT, video_object)
    download_file_size = get_size_of_file(video_path)
    metadata = {
        "meeting_id": mid,
        "meeting_topic": meeting.topic,
        "community": meeting.community,
        "sig": meeting.group_name,
        "agenda": meeting.agenda,
        "record_start": start_time,
        "record_end": end_time,
        "download_url": download_url,
        "total_size": download_file_size,
        "attenders": []
    }
    return metadata


def review_upload_results():
    logger.info('Start to review results for uploading videos to bili')
    bili_client = BiliClient()
    all_b_vid = bili_client.search_all_bili_videos()
    waiting_update_mid = list(Record.objects.filter(url__isnull=True).values_list('mid', flat=True))
    for mid in waiting_update_mid:
        replay_url = Video.objects.get(mid=mid).replay_url
        if not replay_url:
            continue
        b_vid = replay_url.split('/')[-1]
        if b_vid not in all_b_vid:
            logger.info('meeting {}: meeting video had not been passed, waiting...'.format(mid))
            continue
        logger.info('meeting {}: meeting video uploaded to bili passed which b_vid is {}'.format(mid, replay_url))
        Record.objects.filter(mid=mid, platform='bilibili').update(url=replay_url)
    logger.info('review upload results ends......')


# noinspection SpellCheckingInspection
def handle_recording(mid):
    """上传B站和obs的主流程"""
    video_object = get_obs_video_object(mid)
    if not video_object:
        logger.error("{}:not find from video, and user not auto record".format(mid))
        return
    oci = ObsClientImp(settings.ACCESS_KEY_ID, settings.SECRET_ACCESS_KEY, settings.OBS_ENDPOINT)
    get_object_res = oci.get_object(settings.OBS_BUCKETNAME, video_object)
    if get_object_res.status == 200:
        logger.info('{}:{} has been uploaded to OBS, skip...'.format(mid, video_object))
        return
    logger.info('{}: Start to handle recordings...'.format(mid))
    # 1. get recordings of target meeting and download
    meeting = Meeting.objects.get(mid=mid)
    action = MeetingLib.get_prepare_video_action(meeting)
    video_path = handler_meeting(meeting.mplatform, action)
    if not video_path:
        logger.error('{}: video path could not be empty'.format(mid))
        return
    if not os.path.exists(video_path):
        logger.error('{}: fail to download video'.format(mid))
        return
    if os.path.getsize(video_path) == 0:
        logger.error('{}: download but did not get the full video'.format(mid))
        return
    # 2. generate cover image
    cover_path = generate_cover(meeting, video_path)
    if not os.path.exists(cover_path):
        logger.error('{}: fail to generate cover for meeting video'.format(mid))
        return
    # 3. upload video and cover to bili
    meeting_info = {
        'tag': '{}, SIG meeting, recording'.format(meeting.community),
        'title': '{}（{}）'.format(meeting.topic, meeting.date),
        'desc': 'community meeting recording for {}'.format(meeting.group_name)
    }
    bili_client = BiliClient()
    res = bili_client.upload_to_bili(meeting_info, video_path, cover_path)
    if not isinstance(res, dict) or 'bvid' not in res.keys():
        logger.error('{}:Unexpected upload result to bili: {}'.format(mid, res))
        return
    b_vid = res.get('bvid')
    logger.info('{}: upload to bili successfully, bvid is {}'.format(mid, b_vid))
    # 4. save data
    replay_url = bili_client.get_bili_replay_url(b_vid)
    Video.objects.filter(mid=mid).update(replay_url=replay_url)
    if not Record.objects.filter(mid=mid, platform='bilibili'):
        Record.objects.create(mid=mid, platform='bilibili')
    # 5. upload video and cover to OBS
    metadata = generate_video_metadata(mid, video_object, video_path)
    upload_video_res = oci.upload_file(settings.OBS_BUCKETNAME, video_object, video_path, metadata)
    if not isinstance(upload_video_res, dict) or 'status' not in upload_video_res.keys():
        logger.error('{}:Unexpected upload video result to OBS: {}'.format(mid, upload_video_res))
        return
    if upload_video_res.get('status') != 200:
        logger.error('{}:fail to upload video to OBS, the reason is {}'.format(mid, upload_video_res))
        return
    logger.info('{}:start to upload video to OBS')
    upload_cover_res = oci.upload_file_without_metadata(settings.OBS_BUCKETNAME,
                                                        get_obs_cover_object(video_object),
                                                        cover_path)
    if not isinstance(upload_cover_res, dict) or 'status' not in upload_cover_res.keys():
        logger.error('{}:Unexpected upload cover result to OBS: {}'.format(mid, upload_video_res))
        return
    if upload_cover_res.get('status') != 200:
        logger.error('{}:fail to upload cover to OBS, the reason is {}'.format(mid, upload_cover_res))
        return
    logger.info('{}: finish archive'.format(mid))
