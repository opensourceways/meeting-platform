# -*- coding: utf-8 -*-
# @Time    : 2023/10/13 11:47
# @Author  : Tom_zc
# @FileName: common.py
# @Software: PyCharm
import secrets
import string
import subprocess
import threading
import time
import uuid
import tempfile
import os
import logging
import traceback

from datetime import datetime, timedelta
from functools import wraps

from meeting_platform.utils.file_stream import write_content

logger = logging.getLogger('log')


def start_thread(func, m):
    th = threading.Thread(target=func, args=m)
    th.start()


def get_cur_date():
    cur_date = datetime.now()
    return cur_date


def gen_new_temp_dir():
    tmpdir = tempfile.gettempdir()
    while True:
        uuid_str = str(uuid.uuid4())
        new_uuid_str = uuid_str.replace("-", "")
        dir_name = os.path.join(tmpdir, new_uuid_str)
        if not os.path.exists(dir_name):
            return dir_name
        time.sleep(1)


def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def save_temp_img(content):
    dir_name = gen_new_temp_dir()
    make_dir(dir_name)
    tmp_file = os.path.join(dir_name, 'tmp.jpeg')
    write_content(tmp_file, content)
    return dir_name, tmp_file


def get_video_path(mid):
    dir_name = gen_new_temp_dir()
    make_dir(dir_name)
    target_name = mid + '.mp4'
    target_filename = os.path.join(dir_name, target_name)
    return target_filename


def make_nonce():
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def execute_cmd3(cmd, timeout=30, err_log=False):
    """execute cmd3"""
    try:
        p = subprocess.Popen(cmd.split(), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        t_wait_seconds = 0
        while True:
            if p.poll() is not None:
                break
            if timeout >= 0 and t_wait_seconds >= (timeout * 100):
                p.terminate()
                return -1, "", "execute_cmd3 exceeded time {} seconds in executing".format(timeout)
            time.sleep(0.01)
            t_wait_seconds += 1
        out, err = p.communicate()
        ret = p.returncode
        if ret != 0 and err_log:
            logger.error("execute_cmd3 return {}, std output: {}, err output: {}.".format(ret, out, err))
        return ret, out, err
    except Exception as e:
        return -1, "", "execute_cmd3 exceeded raise, e={}, trace={}".format(str(e), traceback.format_exc())


def get_date_by_start_and_end(start_date_str, end_date_str):
    all_date_list = list()
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    date_delta = (end_date - start_date).days
    if date_delta <= 0:
        return all_date_list
    for day in range(0, date_delta + 1):
        cur_date = start_date + timedelta(days=day)
        cur_date_str = cur_date.strftime("%Y-%m-%d")
        all_date_list.append(cur_date_str)
    return all_date_list


def func_retry(tries=3, delay=2):
    def deco_retry(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            for i in range(tries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    logger.error("func_retry e:{}, traceback:{}".format(e, traceback.format_exc()))
                    time.sleep(delay)
            else:
                raise Exception("fun:{} Retries reached".format(fn.__name__))

        return inner

    return deco_retry
