import asyncio
from hashlib import md5
import hashlib
import os
import random
import sys
import time
import json
from typing import Union
from loguru import logger
from urllib.parse import urlencode, urlparse, parse_qsl


from aiohttp import ClientSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Crypto:

    APPKEY = '4409e2ce8ffd12b8'
    APPSECRET = '59b43e04ad6965f34319062b478f83dd'

    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        '''generates md5 hex dump of `str` or `bytes`'''
        if type(data) == str:
            return md5(data.encode()).hexdigest()
        return md5(data).hexdigest()

    @staticmethod
    def sign(data: Union[str, dict]) -> str:
        '''salted sign funtion for `dict`(converts to qs then parse) & `str`'''
        if isinstance(data, dict):
            _str = urlencode(data)
        elif type(data) != str:
            raise TypeError
        return Crypto.md5(_str + Crypto.APPSECRET)


class SingableDict(dict):
    @property
    def sorted(self):
        '''returns a alphabetically sorted version of `self`'''
        return dict(sorted(self.items()))

    @property
    def signed(self):
        '''returns our sorted self with calculated `sign` as a new key-value pair at the end'''
        _sorted = self.sorted
        return {**_sorted, 'sign': Crypto.sign(_sorted)}


def retry(tries=3, interval=1):
    def decorate(func):
        async def wrapper(*args, **kwargs):
            count = 0
            func.isRetryable = False
            log = logger.bind(user=f"{args[0].u.name}")
            while True:
                try:
                    result = await func(*args, **kwargs)
                except Exception as e:
                    count += 1
                    if type(e) == BiliApiError:
                        if e.code == 1011040:
                            raise e
                        elif e.code == 10030:
                            await asyncio.sleep(10)
                        elif e.code == -504:
                            pass
                        else:
                            raise e
                    if count > tries:
                        log.error(f"API {urlparse(args[1]).path} 调用出现异常: {str(e)}")
                        raise e
                    else:
                        # log.error(f"API {urlparse(args[1]).path} 调用出现异常: {str(e)}，重试中，第{count}次重试")
                        await asyncio.sleep(interval)
                    func.isRetryable = True
                else:
                    if func.isRetryable:
                        pass
                        # log.success(f"重试成功")
                    return result

        return wrapper

    return decorate


def client_sign(data: dict):
    _str = json.dumps(data, separators=(',', ':'))
    for n in ["sha512", "sha3_512", "sha384", "sha3_384", "blake2b"]:
        _str = hashlib.new(n, _str.encode('utf-8')).hexdigest()
    return _str


def randomString(length: int = 16) -> str:
    return ''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', length))


class BiliApiError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

    def __str__(self):
        return self.msg


class BiliApi:
    headers = {
        "User-Agent": "Mozilla/5.0 BiliDroid/6.73.1 (bbcallen@gmail.com) os/android model/Mi 10 Pro mobi_app/android build/6731100 channel/xiaomi innerVer/6731110 osVer/12 network/2",
    }
    from .user import BiliUser

    def __init__(self, u: BiliUser, s: ClientSession):
        self.u = u
        self.session = s

    def __check_response(self, resp: dict) -> dict:
        if resp['code'] != 0 or ('mode_info' in resp['data'] and resp['message'] != ''):
            raise BiliApiError(resp['code'], resp['message'])
        return resp['data']

    @retry()
    async def __get(self, *args, **kwargs):
        async with self.session.get(*args, **kwargs) as resp:
            return self.__check_response(await resp.json())

    @retry()
    async def __post(self, *args, **kwargs):
        async with self.session.post(*args, **kwargs) as resp:
            return self.__check_response(await resp.json())

    async def __getraw(self, *args, **kwargs):
        async with self.session.get(*args, **kwargs) as resp:
            return await resp.json()

    async def __postraw(self, *args, **kwargs):
        async with self.session.post(*args, **kwargs) as resp:
            return await resp.json()


    async def loginVerift(self):
        """
        登录验证
        """
        url = "https://app.bilibili.com/x/v2/account/mine"
        params = {
            "access_key": self.u.access_key,
            "actionKey": "appkey",
            "appkey": Crypto.APPKEY,
            "ts": int(time.time()),
        }
        return await self.__get(url, params=SingableDict(params).signed, headers=self.headers)

    async def callraw(self, params):
        """
        API代理
        """
        url = params["url"]
        method = params["method"] or "GET"
        content_type = params['headers'] and params['headers']['Content-Type'] or "application/x-www-form-urlencoded"
        body = {}
        if content_type == "application/x-www-form-urlencoded":
            body = dict(parse_qsl(params['body']))
        elif content_type == "application/json":
            body = json.loads(params['body'])
        body.update({
            "access_key": self.u.access_key,
            "actionKey": "appkey",
            "appkey": Crypto.APPKEY,
            "ts": int(time.time()),
        })

        _headers = self.headers.copy()
        _headers.update({"Content-Type": content_type})

        if method.upper() == "GET":
            return await self.__getraw(
                url,
                params=SingableDict(body).signed,
                headers=_headers
            )
        elif method.upper() == "POST":
            return await self.__postraw(
                url,
                data=SingableDict(body).signed,
                headers=_headers
            )

        


