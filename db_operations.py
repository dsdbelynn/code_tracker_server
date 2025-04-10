import sqlite3
from datetime import datetime

db_file = 'database.db'

# 游戏配置中心化
GAME_CONFIGS = {
    "InfinityNikki": {
        "table_name": "InfinityNikkiCode",
        "weibo_uids": ['7801655101',],
        "api_endpoint": "infinity"
    },
    "ShiningNikki": {
        "table_name": "ShiningNikkiCode", 
        "weibo_uids": ['6498105282'],
        "api_endpoint": "shining"
    },
    "DeepSpace": {
        "table_name": "DeepSpaceCode",
        "weibo_uids": ['7484247626'],
        "api_endpoint": "deepspace"
    }
}

def init_database():
    """初始化SQLite数据库，创建必要的表"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 创建时间跟踪表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS LastCheckTime (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game TEXT UNIQUE,
        last_check_time TEXT
    )
    ''')
    
    # 为每个游戏创建表
    for game_name, config in GAME_CONFIGS.items():
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {config["table_name"]} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            reward TEXT,
            time TEXT,
            url TEXT,
            start TEXT,
            end TEXT
        )
        ''')
        
        # 初始化时间记录（如果不存在）
        cursor.execute('SELECT COUNT(*) FROM LastCheckTime WHERE game = ?', (game_name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO LastCheckTime (game, last_check_time) VALUES (?, ?)', 
                          (game_name, datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

def save_game_code(game_name, code_data):
    """将兑换码保存到对应游戏的表中"""
    table_name = GAME_CONFIGS[game_name]["table_name"]
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    if code_data['key'] != "":
        cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE key = ?', (code_data['key'],))
        if cursor.fetchone()[0] > 0:
            print(f"兑换码 {code_data['key']} 已存在，跳过添加")
            conn.close()
            return False
    
    cursor.execute(f'''
    INSERT INTO {table_name} (key, reward, time, url, start, end)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (code_data['key'], code_data['reward'], code_data['time'], 
          code_data['url'], code_data['start'], code_data['end']))
    
    conn.commit()
    conn.close()
    print(f"兑换码 {code_data['key']} 已成功添加到数据库")
    return True

def get_game_codes(game_name):
    """获取指定游戏的兑换码"""
    table_name = GAME_CONFIGS[game_name]["table_name"]
    
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(f'SELECT key, reward, time, url, start, end FROM {table_name} ORDER BY time DESC')
    rows = cursor.fetchall()
    
    codes = []
    for row in rows:
        codes.append({
            'code': row['key'],
            'reward': row['reward'],
            'date': row['time'],
            'url': row['url'],
            'start': row['start'],
            'end': row['end']
        })
    
    conn.close()
    return codes

def update_check_time(game):
    """更新数据库中指定游戏的最后检查时间"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('UPDATE LastCheckTime SET last_check_time = ? WHERE game = ?', 
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), game))
    conn.commit()
    conn.close()

def get_last_check_time(game):
    """从数据库获取指定游戏的最后检查时间"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT last_check_time FROM LastCheckTime WHERE game = ?', (game,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

if __name__ == "__main__":
    init_database()