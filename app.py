# app.py
import eventlet
eventlet.monkey_patch()  # 必须在其他导入前调用

from flask import Flask, jsonify, send_from_directory, request
import sqlite3
import os
from datetime import datetime
import webbrowser
import threading
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
import time
import requests  # 新增：用于发送请求
from flask_socketio import SocketIO, emit

# 创建 Flask 应用后初始化 SocketIO
app = Flask(__name__, static_url_path='', static_folder='public')
# 修改app.py中的socketio初始化
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',  # 明确指定使用eventlet
    logger=False,  # 启用详细日志
    engineio_logger=False  # 启用引擎日志
)

# 添加 WebSocket 事件处理函数
@socketio.on('connect')
def handle_connect():
    print('客户端已连接')

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')
    
# 修改notify_new_code函数
def notify_new_code(game_name, json):
    print(f"通知客户端新的{game_name}兑换码...")
    try:
        # 直接使用emit并广播到所有客户端
        
        socketio.emit('new_code', {'game_name': game_name, 'key': json["key"]})
        print("Socket.IO事件已发送")
    except Exception as e:
        print(f"Socket.IO发送失败: {str(e)}")


# 启动RSSHub的函数
def start_rsshub():
    rsshub_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'RssHub'))
    print(f"启动RSSHub，路径: {rsshub_path}")
    
    process = subprocess.Popen(
        'cmd /c npm run start', 
        cwd=rsshub_path,
        shell=True,
        stdout=None,
        stderr=None
    )
    print(f"RSSHub已启动，进程ID: {process.pid}")
    return process

# 新增：检查RSSHub是否可用的函数
def is_rsshub_ready():
    try:
        # 假设RSSHub在本地1200端口运行，可根据实际情况调整
        response = requests.get('http://localhost:1200/', timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

# 数据库文件路径
DB_FILE = 'database.db'

# 定义一个函数，顺序获取所有游戏的兑换码
def fetch_all_redemption_codes():
    
    # 导入从code_tracker.py中定义的函数
    from code_tracker import (
        fetch_infinity_nikki_redemption_codes,
        fetch_shining_nikki_redemption_codes,
        fetch_deep_space_redemption_codes
    )
    
    # 获取无限未来兑换码
    print("正在获取无限暖暖(InfinityNikki)兑换码...")
    fetch_infinity_nikki_redemption_codes()
    
    # 获取闪耀暖暖兑换码
    print("正在获取闪耀暖暖(ShiningNikki)兑换码...")
    fetch_shining_nikki_redemption_codes()
    
    # 获取深空之眠兑换码
    print("正在获取恋与深空(DeepSpace)兑换码...")
    fetch_deep_space_redemption_codes()
    
    print("所有游戏兑换码获取完毕")

# 提供静态文件
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

# 获取游戏兑换码的API端点
@app.route('/api/codes/<game>')
def api_get_game_codes(game):
    # 游戏名称映射
    game_mapping = {
        'infinity': 'InfinityNikki',
        'shining': 'ShiningNikki',
        'deepspace': 'DeepSpace'
    }
    
    if game not in game_mapping:
        return jsonify({"error": "无效的游戏名称"}), 404
        
    # 从db_operations.py导入获取兑换码的函数
    from db_operations import get_game_codes
    
    game_name = game_mapping[game]
    codes = get_game_codes(game_name)
    return jsonify(codes)

@app.route('/test_emit/<game>/<code>')
def test_emit(game, code):
    notify_new_code(game, code)
    return f'已发送测试事件: {game} - {code}'
    
if __name__ == '__main__':
    # 先启动RSSHub
    rsshub_process = start_rsshub()

    # 等待RSSHub启动完成
    print("等待RSSHub启动...")
    
    # 替换固定等待时间为请求检查
    max_attempts = 30  # 最大尝试次数
    attempt = 0
    while True:
        if is_rsshub_ready():
            print("RSSHub已成功启动！")
            break
        print(f"RSSHub尚未就绪，尝试 {attempt+1}...")
        attempt += 1
        time.sleep(5)  # 每5秒检查一次

    # 确保数据库已初始化
    from db_operations import init_database
    init_database()
    
    # 创建调度器
    scheduler = BackgroundScheduler()
    
    # 设置定时任务，每小时执行一次所有游戏的兑换码获取
    scheduler.add_job(fetch_all_redemption_codes, 'cron', minute=1, id='fetch_all_codes_job')
    
    # 启动调度器
    scheduler.start()
    
    # 在程序退出时关闭调度器
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
    # 启动时也执行一次所有游戏的兑换码获取
    threading.Timer(5.0, fetch_all_redemption_codes).start()
    
    # 启动Flask应用
    try:
        socketio.run(app, host='0.0.0.0', port=3000, debug=False)
    finally:
        # 关闭 RSSHub 进程
        if rsshub_process:
            print("关闭RSSHub进程...")
            rsshub_process.terminate()
