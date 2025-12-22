import os
import json
from flask import Flask, send_from_directory, request, jsonify
from datetime import datetime

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
DATA_FILE = os.path.join(base_dir, 'practice_log.json') # 設定存檔的檔案名稱

# 1. 讀取首頁
@app.route('/')
def home():
    files = os.listdir(base_dir)
    html_files = [f for f in files if f.endswith('.html')]
    target_file = html_files[0] if html_files else '吉他新手工作坊.html'
    return send_from_directory(base_dir, target_file)

# 2. 【核心功能】接收前端傳來的練習紀錄 (存檔)
@app.route('/api/save_log', methods=['POST'])
def save_log():
    data = request.json # 抓取 JS 傳來的資料
    # data 會長這樣: {'date': '2025-01-10 10:00', 'duration': '05:30'}
    
    # 讀取舊紀錄
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                records = json.load(f)
            except:
                pass # 如果檔案壞掉就當作空的
    
    # 加入新紀錄
    records.insert(0, data) # 把最新的插在最前面
    
    # 寫入檔案
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)
        
    return jsonify({"status": "success", "message": "紀錄已儲存！"})

# 3. 【核心功能】回傳所有紀錄給前端 (讀檔)
@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    if not os.path.exists(DATA_FILE):
        return jsonify([]) # 沒檔案就回傳空陣列
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            records = json.load(f)
            return jsonify(records)
        except:
            return jsonify([])

# 4. 處理靜態檔案
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(base_dir, filename)

if __name__ == '__main__':
    app.run(debug=True, port=8000)