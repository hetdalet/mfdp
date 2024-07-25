import collections
import json
import os
import random
import time
import urllib.parse as urlparse
from uuid import UUID

import httpx
import redis

TG_BOT_POLL_TIMEOUT = int(os.getenv("TG_BOT_POLL_TIMEOUT"))
TG_BOT_POLL_MAX_RETRIES = int(os.getenv("TG_BOT_POLL_MAX_RETRIES"))


class API:

    def __init__(self, host, port, cookies=None):
        self._host = host
        self._port = port
        self._cookies = cookies or {}
        self._authority = f"http://{host}:{port}"

    def get(self, route, params=None, cookies=None):
        cookies = cookies or self._cookies
        return httpx.get(self._get_url(route, params), cookies=cookies)

    def post(self, route, data=None, cookies=None):
        data = data or {}
        cookies = cookies or self._cookies
        return httpx.post(self._get_url(route), json=data, cookies=cookies)

    def _get_url(self, route, params=None):
        params = [
            f"{name}={val}"
            for name, val in (params or {}).items()
        ]
        if params:
            params = "&".join(params)
            route = f"{route}?{params}"
        url = urlparse.urljoin(self._authority, route)
        return url


Session = collections.namedtuple(
    "Session",
    (
        "api_user_id",
        "cookie",
        "chat_id",
        "message_id",
        "state",
        "input"
    )
)
core_api = API(
    host=os.getenv("APP_HOST"),
    port=os.getenv("APP_PORT"),
)


def get_rds():
    rds = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        decode_responses=True
    )
    return rds


def get_session(user_id: int):
    session = _get_session(user_id)
    if not session:
        return
    session = Session(
        api_user_id=session["user_id"],
        cookie=session["cookie"],
        state=session.get("state"),
        input=session.get("input"),
        chat_id=session.get("chat_id"),
        message_id=session.get("message_id"),
    )
    return session


def _get_session(user_id: int):
    rds = get_rds()
    try:
        session = rds.get(str(user_id))
    finally:
        rds.close()
    if not session:
        return {}
    session = json.loads(session)
    return session


def update_session(user_id: int, update: dict):
    session = _get_session(user_id)
    if not session:
        return
    session.update(update)
    rds = get_rds()
    try:
        rds.set(str(user_id), json.dumps(session))
    finally:
        rds.close()


def get_account_balance(user_id: int):
    session = get_session(user_id)
    response = core_api.get(
        f"/users/{session.api_user_id}/account",
        cookies=session.cookie,
    )
    if response.status_code == 200:
        result = response.json()['balance']
    else:
        result = response.json()['detail']
    return response.status_code, result


def poll_task(key: UUID, cookies):
    retry_count = 0
    while retry_count < TG_BOT_POLL_MAX_RETRIES:
        retry_count += 1
        jitter = random.randint(0, 10) / 100
        time.sleep(TG_BOT_POLL_TIMEOUT + jitter)
        response = core_api.get(f"/tasks/{key}", cookies=cookies)
        status = response.status_code
        print('POLL_TASK', response.json(), flush=True)
        if status != 200 or response.json()["end"] is not None:
            break
    return response
