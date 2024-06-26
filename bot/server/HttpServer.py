import json
import logging
import time
import traceback

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bot.server.RequestHandler import RequestHandler

log = logging.getLogger(__name__)

app = FastAPI()
request_handler = RequestHandler()

# 创建一个FIFO链式数据表缓存
callbackMes = []
lastPullTime = time.time()


@app.get('/')
def index():
    return "Hello World"


@app.post('/weixinCallback')
async def weixinCallback(request: Request):
    user_input = await request.json()
    # 当前时间和最后一次拉取时间间隔5分钟，则追加消息
    global lastPullTime, callbackMes
    if lastPullTime is not None and time.time() - lastPullTime < 300:
        callbackMes.append(user_input)
    else:
        callbackMes = []
    print(user_input)
    request_handler.handle_weixin_callback(user_input)
    return {"response": "success"}


@app.get('/weixinCallback')
def weixinCallbackMsg():
    global lastPullTime
    lastPullTime = time.time()
    if callbackMes:
        message = callbackMes.pop(0)
        logging.info('Message retrieved and removed from FIFO queue')
        return json.dumps(message), 200
    return '', 200


# 定义全局异常处理器
@app.exception_handler(Exception)
def handle_exception(request: Request, exc: Exception):
    # 获取异常的堆栈信息
    exc_info = traceback.format_exc()
    # 记录错误日志
    logging.error(f"Unhandled Exception: {type(exc).__name__}: {exc}\n{exc_info}")
    # 返回错误响应
    return JSONResponse(status_code=500, content={"message": f"An error occurred: {exc}"})


def runHttpServer():
    host = "0.0.0.0"
    port = 18000
    # 定义该程序的接口地址，用于让微信回调到接口中
    callBackHttpUrl = f"http://127.0.0.1:{port}/weixinCallback"
    # 初始化微信回调地址，一定要先初始化，再启动程序，把这一行下移一行就不执行了
    request_handler.init_weixin_callbackUrl(callBackHttpUrl)
    # 启动程序
    uvicorn.run(app, host=host, port=port)
