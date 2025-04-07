import os
import re
import feedparser
import calendar
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
import json
import requests

# 导入数据库操作函数和游戏配置
from db_operations import (
    init_database, save_game_code, update_check_time, 
    get_last_check_time, GAME_CONFIGS
)

def format_published_date(entry, default="2000-01-01 00:00:00"):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            timestamp = calendar.timegm(entry.published_parsed)
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            local_dt = dt.astimezone()     
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        return default
    except Exception as e:
        print(f"日期格式化错误: {e}")
        return default

def get_weibo_rss_content(uid) -> Optional[dict]:
    load_dotenv()
    rss_base_url = os.getenv('RSS_SOURCE', "http://192.168.137.250:1200")
    url = f"{rss_base_url}/weibo/user/{uid}/showRetweeted=0"
    try:
        feed = feedparser.parse(url)
        if feed.get('bozo_exception') or (hasattr(feed, 'status') and feed.status != 200):
            return None            
        return feed
    except Exception:
        return None

def process_with_deepseek(text):
    load_dotenv()
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    str = """
    {
        "key" : "ABC",
        "reward" : "钻石*100 + 金币*100",
        "start": "2020/01/01 00:00:00",
        "end": "2030/12/31 23:59:59"
    }
    """

    try:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_BASE
        )
        
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"请分析以下文本，找到其中包含的兑换码，福利内容，生效时间起始和截止，并直接根据我的示范输出，示范：{str}，严格遵守示范的格式，不要添加额外的字符，其中reward=福利内容，key=提取出来的兑换码（不要输出成\"兑换码:AAA\",直接输出成AAA），start=起始时间，end=结束时间，时分秒月日都要保证是两位数字注意补零。请尽可能的找到，如果没有找到则键值留空。不要添加类似'''json 的头尾\n\n{text}"
                }
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek API调用失败: {e}")
        return None

def send_code_notification(game_name, key):
    """通过HTTP调用测试路由发送兑换码更新事件"""
    print(f"通过HTTP接口通知客户端新的{game_name}兑换码...")
    try:
        url = f"http://127.0.0.1:3000/test_emit/{game_name}/{key}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"HTTP通知成功: {response.text}")
            return True
        else:
            print(f"HTTP通知失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"HTTP通知出错: {e}")
        return False

def fetch_game_redemption_codes(game_name):
    """通用的游戏兑换码获取函数"""
    init_database()
    last_check_time = get_last_check_time(game_name)
    flag = 0
    
    if (datetime.now() - datetime.strptime(last_check_time, "%Y-%m-%d %H:%M:%S")).total_seconds() < 3600:
        print(f"{game_name}: 一小时内刚获取过，不执行")
    else:
        print(f"开始执行 {game_name} 的RSS订阅")
        weibo_uids = GAME_CONFIGS[game_name]["weibo_uids"]
        
        for uid in weibo_uids:
            rss_data = get_weibo_rss_content(uid)
            if rss_data is None:
                print(f"{game_name} UID {uid}: 没有获取到数据")
                continue
                
            items = rss_data.entries
            for item in items:
                time_str = format_published_date(item)
                if datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S") < datetime.strptime(last_check_time, "%Y-%m-%d %H:%M:%S"):
                    # 说明已经处理过了
                    continue
                else:
                    description = re.compile(r"<[^>]+>").sub(' ', item.description)
                    if "兑换码" in description:
                        # 处理含兑换码的内容
                        ret = process_with_deepseek(description)
                        print(ret)
                        try:
                            data = json.loads(ret)
                            code = {
                                "key": data["key"],
                                "reward": data["reward"].replace(" ", ""),
                                "start": data["start"],
                                "end": data["end"],
                                "time": time_str,
                                "url": item.link  # 添加链接信息
                            }
                            print(code)
                            # 保存到数据库
                            save_game_code(game_name, code)
                            send_code_notification(game_name, code["key"])
                            flag = 1
                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误: {e}")
                        except Exception as e:
                            print(f"处理数据时出错: {e}")
                    else:
                        continue
        if flag == 1:
            update_check_time(game_name)
        else:
            print("没有新的兑换码")


# 为了保持向后兼容性的包装函数
def fetch_infinity_nikki_redemption_codes():
    return fetch_game_redemption_codes("InfinityNikki")

def fetch_shining_nikki_redemption_codes():
    return fetch_game_redemption_codes("ShiningNikki")

def fetch_deep_space_redemption_codes():
    return fetch_game_redemption_codes("DeepSpace")

if __name__ == "__main__":
    fetch_infinity_nikki_redemption_codes()