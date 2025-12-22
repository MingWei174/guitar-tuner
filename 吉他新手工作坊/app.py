import os
import json
from flask import Flask, send_from_directory, request, jsonify

# 1. 設定基本路徑
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
DATA_FILE = os.path.join(base_dir, 'practice_log.json')

# 2. 首頁：增加「檔案檢查」與「偵錯輸出」功能
@app.route('/')
def home():
    # 取得目前資料夾內的所有檔案
    all_files = os.listdir(base_dir)
    # 篩選出 .html 結尾的檔案
    html_files = [f for f in all_files if f.endswith('.html')]
    
    # 情況 A：完全找不到 HTML 檔
    if not html_files:
        return (
            f"<h1>❌ 找不到任何網頁檔案 (404 Error)</h1>"
            f"<h3>請檢查以下事項：</h3>"
            f"<ul>"
            f"<li>目前的程式執行資料夾是：<b>{base_dir}</b></li>"
            f"<li>這個資料夾裡面只有這些檔案：<br>{all_files}</li>"
            f"<li><b>解決方法：</b>請確認你的 HTML 檔 (例如 '吉他新手工作坊.html') 是否有放在這個資料夾裡。</li>"
            f"</ul>"
        )
    
    # 情況 B：找到了，嘗試開啟第一個
    target_file = html_files[0]
    full_path = os.path.join(base_dir, target_file)
    
    print(f"👉 偵測到網頁檔案：{target_file}")
    
    if os.path.exists(full_path):
        return send_from_directory(base_dir, target_file)
    else:
        return f"<h1>❌ 檔案存在但無法讀取</h1><p>路徑：{full_path}</p>"

# 3. 儲存紀錄 API
@app.route('/api/save_log', methods=['POST'])
def save_log():
    try:
        data = request.json
        records = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    records = json.load(f)
                except:
                    pass
        records.insert(0, data)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "success", "message": "紀錄已儲存！"})
    except Exception as e:
        print(f"存檔錯誤: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 4. 讀取紀錄 API
@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    if not os.path.exists(DATA_FILE):
        return jsonify([])
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            records = json.load(f)
            return jsonify(records)
        except:
            return jsonify([])

# 5. 靜態檔案處理
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(base_dir, filename)

if __name__ == '__main__':
    print("="*50)
    print(f"🚀 伺服器啟動中...")
    print(f"📂 執行目錄: {base_dir}")
    print(f"👉 請打開網址: http://127.0.0.1:8000/")
    print("="*50)
    app.run(debug=True, port=8000)