import os, time
import uuid
import asyncio
from aiohttp import web
import aiohttp_cors
import aiohttp_jinja2
import jinja2
from loguru import logger
import config
from src import BiliUser

log = logger.bind(user="B站应用代理服务器")
__VERSION__ = "0.0.2"

routes = web.RouteTableDef()


@routes.get('/', name="index")
@aiohttp_jinja2.template('index.html')
async def setup_handler(request: web.Request):
    request.match_info.route.name
    authkey = request.url.query.get('key')
    bili_users = request.app['bili_users']
    return {'key': authkey, 
            'biliusers': [{'uid':uid, 'name':bili_users[uid].name} for uid in bili_users.keys()],
            'proxy_url': request.url.join(request.app.router['proxy'].url_for().with_query({"key": authkey}))}


@routes.get('/setup', name="setup")
@routes.post('/setup', name="setup")
@aiohttp_jinja2.template('setup.html')
async def setup_handler(request: web.Request):
    authkey = request.url.query.get('key')
    conf = request.app['config']
    bili_users = request.app['bili_users']
    if request.method == 'POST':
        update_flag = False
        form = await request.post()
        action = form.get("action")
        access_keys = form.get("access_key")
        uid = form.get("uid")
        if action == "login_biliuser" and access_keys:
            for access_key in access_keys.replace(" ", "").splitlines():
                if not access_key:
                    continue
                existed = False
                for uid in bili_users.keys():
                    if access_key == bili_users[uid].access_key:
                        existed = True
                        break
                if not existed:
                    biliuser = BiliUser(access_key)
                    await biliuser.init()
                    if biliuser.isLogin:
                        if biliuser.mid in bili_users:
                            await bili_users[biliuser.mid].logout()
                        bili_users[biliuser.mid] = biliuser
                        conf['USERS'] = [{"access_key": biliuser.access_key} for biliuser in bili_users.values()]
                        update_flag = True
        if action == "logout_biliuser" and uid:
            mid = int(uid)
            biliuser = bili_users.pop(mid, None)
            if biliuser:
                await biliuser.logout()      
                del biliuser          
                conf['USERS'] = [{"access_key": biliuser.access_key} for biliuser in bili_users.values()]
                update_flag = True
        elif action == "rest_token":
            authkey = uuid.uuid4().hex
            conf['KEY'] = authkey
            update_flag = True
        if update_flag:
            save_config(conf)
        location = request.app.router['setup'].url_for().with_query({"key": authkey})
        raise web.HTTPFound(location=location) # request.path_qs
    return {'key': authkey, 
            'biliusers': [{'uid': uid, 'name': bili_users[uid].name} for uid in bili_users.keys()]}


@routes.get('/test', name="test")
@aiohttp_jinja2.template('test.html')
async def test_handler(request: web.Request):
    authkey = request.url.query.get('key')
    bili_users = request.app['bili_users']
    return {'key': authkey, 
            'biliusers': [{'uid': uid, 'name': bili_users[uid].name} for uid in bili_users.keys()]}


@routes.post('/proxy', name="proxy")
async def proxy_handler(request: web.Request):
    data = await request.json()
    res = {"code": -401, "message": "未认证 (或非法请求)", "ttl": 1}
    authkey = data.get('_key') or request.url.query.get('key')
    if authkey == request.app['config']['KEY']:
        if data.get('_uid') in request.app['bili_users']:
            if data.get('url') and data['body']:
                biliuser = request.app['bili_users'][data['_uid']]
                params = { key: data[key] for key in data.keys() if key not in ['_uid', '_key'] }
                res = await biliuser.callapi(params)
            else:
                res = {"code": 0, "message": "0", "ttl": 1}
        else:
            res = {"code": -101, "message": "账号未登录", "ttl": 1}
    return web.json_response(res)


@aiohttp_jinja2.template('anonymous.html')
async def anonymous_handler(request: web.Request):
    return {'key': ''}


@web.middleware
async def middleware_auth(request: web.Request, handler):
    resource = request.match_info.route.resource
    if resource and resource.name not in ["static", "proxy"]:
        authkey = request.url.query.get('key')
        if authkey != request.app['config']['KEY']:
            return await anonymous_handler(request)
    return await handler(request)


def get_config():
    try:
        return config.load_yaml(os.path.join(config.BASE_PATH, 'users.yaml'))            
    except Exception as e:
        log.error("读取配置文件失败,请检查配置文件格式是否正确: {e}")


def save_config(conf: dict):
    try:
        return config.dump_yaml(os.path.join(config.BASE_PATH, 'users.yaml'), conf)
    except Exception as e:
        log.error("写入配置文件失败！")  


async def init_users(app: web.Application):
    conf = app['config']
    biliusers = {}
    for user in conf['USERS']:
        if user['access_key']:
            biliuser = BiliUser(user['access_key'])
            await biliuser.init()
            if biliuser.isLogin:
                biliusers[biliuser.mid] = biliuser
            await asyncio.sleep(0.1)
    app['bili_users'] = biliusers
    app['start_ts'] = int(time.time()*1000)
    log.info('配置读取完毕,开启服务')
    log.info('当前服务令牌: '+conf['KEY'])


def main():
    conf = get_config()
    if not conf:
        log.error("读取配置文件失败,请检查配置文件格式是否正确")
        return
    app = web.Application()
    app['title'] = 'B站应用代理服务器'
    app['version'] = __VERSION__
    app['config'] = conf
    app['nav'] = [('index', '首页'), ('setup', '配置'), ('test', '测试')]
    aiohttp_jinja2.setup(app,
        context_processors=[aiohttp_jinja2.request_processor],
        loader=jinja2.FileSystemLoader(os.path.join(config.BASE_PATH, 'templates')))
    app.middlewares.append(middleware_auth)
    app.add_routes(routes)
    app.add_routes([web.static('/static', os.path.join(config.BASE_PATH, 'static'), name='static')])
    app['static_root_url'] = '/static'
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    for route in list(app.router.routes()):
        cors.add(route)
    app.on_startup.append(init_users)
    web.run_app(app, host=app['config']['HOST'], port=app['config']['PORT'])


if __name__ == "__main__":
    main()