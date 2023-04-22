from aiohttp import web
import aiohttp_cors
import aiohttp_jinja2
import jinja2

import os

from loguru import logger
import config
from src import BiliUser

log = logger.bind(user="B站应用代理服务器")
__VERSION__ = "0.0.1"

routes = web.RouteTableDef()

@routes.get('/u/{uid}')
async def uid_handler(request):
    authkey = request.rel_url.query.get('key')
    if authkey == request.app['config']['KEY']:
        uid = int(request.match_info.get('uid', 0))
        if uid in request.app['bili_users']:
            text = "Hello, "  + request.app['bili_users'][uid].name
        else:
            text = "Sorry, This account is not authorized to login!"
    else:
        text = "Hello, Anonymous"
    return web.Response(text=text)

@routes.get('/test', name="test")
async def test_handler(request):
    authkey = request.rel_url.query.get('key')
    if authkey == request.app['config']['KEY']:
        accounts = []
        for uid in request.app['bili_users'].keys():
            accounts.append({'uid':uid, 'name':request.app['bili_users'][uid].name})
        context = {'key': authkey, 
                   'accounts': accounts, 
                   'proxy_url': request.url.join(request.app.router['proxy'].url_for().with_query({"key": authkey}))}
        return aiohttp_jinja2.render_template('test.html', request, context)
    else:
        text = "Hello, Anonymous"
        return web.Response(text=text)

@routes.post('/proxy', name="proxy")
async def proxy_handler(request):
    argv = request.rel_url.query
    data = await request.json()
    res = {}
    authkey = data['_key'] or argv.get('key')
    if authkey == request.app['config']['KEY']:
        if data['_uid'] in request.app['bili_users']:
            biliuser = request.app['bili_users'][data['_uid']]
            params = { key: data[key] for key in data.keys() if key not in ['_uid', '_key'] }
            res = await biliuser.callapi(params)
    return web.json_response(res)

def getconfig():
    try:
        return config.load_yaml(os.path.join(config.BASE_PATH, 'users.yaml'))            
    except Exception as e:
        log.error("读取配置文件失败,请检查配置文件格式是否正确: {e}")

async def init_users(app):
    conf = app['config']
    biliusers = {}
    for user in conf['USERS']:
        if user['access_key']:
            biliuser = BiliUser(user['access_key'])
            await biliuser.init()
            if biliuser.isLogin:
                biliusers[biliuser.mid] = biliuser
    app['bili_users'] = biliusers
    log.info('配置读取完毕,开启服务')
    log.info('测试页面：'+str(app.router['test'].url_for().with_query({"key": conf['KEY']})))
    log.info('代理服务地址：'+str(app.router['proxy'].url_for().with_query({"key": conf['KEY']})))

def main():
    conf = getconfig()
    if not conf:
        log.error("读取配置文件失败,请检查配置文件格式是否正确")
        return
    app = web.Application()
    app['config'] = conf
    aiohttp_jinja2.setup(app,
        loader=jinja2.FileSystemLoader(os.path.join(config.BASE_PATH, 'templates')))
    app.add_routes(routes)
    app.add_routes([web.static('/static', os.path.join(config.BASE_PATH, 'static'))])
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