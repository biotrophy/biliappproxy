from aiohttp import ClientSession, ClientTimeout
import sys
import os
import uuid
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> <blue> {extra[user]} </blue> <level>{message}</level>",
    backtrace=True,
    diagnose=True,
)

class BiliUser:
    def __init__(self, access_token: str, config: dict = {}):
        from .api import BiliApi

        self.mid, self.name = 0, ""
        self.access_key = access_token  # 登录凭证

        self.session = ClientSession(timeout=ClientTimeout(total=3))
        self.api = BiliApi(self, self.session)

        self.errmsg = ["错误日志："]
        self.uuids = [str(uuid.uuid4()) for _ in range(2)]
        
        self.isLogin = False

    async def loginVerify(self) -> bool:
        """
        登录验证
        """
        if not self.access_key:
            return False
        loginInfo = await self.api.loginVerift()
        self.mid, self.name = loginInfo['mid'], loginInfo['name']
        self.log = logger.bind(user=self.name)
        if loginInfo['mid'] == 0:
            self.isLogin = False
            return False
        self.log.log("SUCCESS", str(loginInfo['mid']) + " 登录成功")
        self.isLogin = True
        return True

    async def callapi(self, params):
        return await self.api.callraw(params)

    async def init(self):
        if not await self.loginVerify():
            self.log.log("ERROR", "登录失败 可能是 access_key 过期 , 请重新获取")
            self.errmsg.append("登录失败 可能是 access_key 过期 , 请重新获取")
            await self.session.close()

    async def logout(self):
        await self.session.close()
        self.log.log("WARNING", str(self.mid) + " 退出登录")

