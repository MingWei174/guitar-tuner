import requests
from bs4 import BeautifulSoup
import pandas as pd
import re # 新增：用來抓取年份數字的正則表達式
import time
import random
from datetime import datetime, timedelta

# --- 新增：引入 Rich 模組 ---
from rich.console import Console
from rich.table import Table
from rich import box  # 用來設定表格邊框樣式

# 初始化 Rich 的控制台
console = Console()


def get_status_by_date(soup, year):
    """
    核心邏輯：從內頁找出最新一集的日期，判斷是否完結
    """
    try:
        # 1. 抓取所有集數的區塊 (通常在 section.season 裡面)
        # 巴哈的結構通常是 <div class="season"> ... <a>...<span class="date">12/08</span></a>
        # 我們直接用 regex 在整個網頁文字中找 "MM/DD" 這種格式的日期
        # 這種暴力法最通用，不用怕 class 改名
        
        text_content = soup.get_text()
        
        # 尋找所有像 "12/08" 或 "01/05" 這樣的日期
        date_matches = re.findall(r'(\d{1,2})/(\d{1,2})', text_content)
        
        if not date_matches:
            return "連載中" # 抓不到日期，保守起見當作連載中

        # 2. 轉換日期並找出「離現在最近」的一個日期
        latest_date = None
        today = datetime.now()
        
        for match in date_matches:
            month, day = int(match[0]), int(match[1])
            
            # 簡單防呆：月份不能超過 12
            if month > 12 or month < 1: continue

            # 組合年份：如果是 12月，而現在是 1月，那可能是去年的 12月
            # 但為了簡化，我們先假設都是當年度 (2025) 的日期
            # 除非該番是跨年份的 (這部分邏輯可以寫更細，但期末專題先不用太複雜)
            try:
                date_obj = datetime(year, month, day)
                
                # 更新 logic: 找出最接近今天，但不是未來的日期 (有些預告會有未來日期)
                if date_obj <= today:
                    if latest_date is None or date_obj > latest_date:
                        latest_date = date_obj
            except:
                continue
        
        if latest_date is None:
            return "連載中"

        # 3. 【關鍵判斷】 兩週法則
        days_diff = (today - latest_date).days
        print(f"    -> 最新一集日期: {latest_date.strftime('%m/%d')}, 距離今天 {days_diff} 天")
        
        if days_diff > 14:
            return "已完結"
        else:
            return "連載中"

    except Exception as e:
        print(f"    日期判斷錯誤: {e}")
        return "連載中" # 發生錯誤時的預設值
    

def get_anime_details(link, year):
    """
    爬取巴哈姆特動畫瘋的列表資料
    """
    url = "https://ani.gamer.com.tw/animeList.php?sort=2" # sort=1 代表依年份排序 # sort=2 代表依月人氣排序(我要的,才能抓到以前的神作)
    
    # 2. 技術重點：User-Agent 偽裝 (將在報告中提及) # 修改 Headers：加入 Cookie 偽裝成已滿 18 歲的使用者
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Cookie": "over18=1"  # <--- 關鍵！加入這一行
    }
    
    try:
        # 隨機休息 0.5 ~ 1.5 秒，模擬人類點擊，避免被鎖
        time.sleep(random.uniform(0.5, 1.5)) 
        res = requests.get(link, headers=headers, timeout=10)
        if res.status_code != 200:
            return 0.0
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 1. 抓評分
        score_div = soup.find("div", class_="score-overall-number")
        score = float(score_div.text.strip()) if score_div else 0.0
        
        # 2. 抓狀態 (使用上面的時間判斷邏輯)
        # 如果是舊番(2024以前)，直接回傳已完結，不用浪費時間算日期
        current_year = datetime.now().year
        if isinstance(year, int) and year < current_year:
            real_status = "已完結"
        else:
            # 如果是今年(2025)的，才去分析日期
            real_status = get_status_by_date(soup, year if isinstance(year, int) else current_year)
        
        # --- 3. 抓取標籤 (終極修正) ---
        tags = []
        
        # 策略 A: 使用 CSS Selector 直接找 class="tag" 的 li
        # 這是最通用的方法，不管 ul 叫什麼名字都能抓到
        tag_elements = soup.select("li.tag")
        
        if tag_elements:
            tags = [t.text.strip() for t in tag_elements]
        else:
            # 策略 B: 如果策略 A 失敗，嘗試抓取 "作品分類" 附近的文字 (備用方案)
            # 有時候 requests 抓到的 HTML 結構比較亂，用文字定位
            try:
                data_intro = soup.find("div", class_="data_intro")
                if data_intro:
                    # 這裡面通常包含標籤，試著找裡面的連結文字
                    links = data_intro.find_all("a")
                    # 過濾掉非標籤的連結 (通常標籤連結包含 search.php?keyword=)
                    tags = [a.text.strip() for a in links if "keyword=" in a.get("href", "")]
            except:
                pass

        # Debug: 真的抓不到才印
        if not tags:
            print(f"   [警告] {link} 真的抓不到標籤！")

        tags_str = ",".join(tags)

        return score, real_status, tags_str
            
    except Exception as e:
        print(f"內頁錯誤: {e}")
        return 0.0, "連載中"

def get_anime_data_v3(max_pages=11):
    """
    升級版：支援翻頁 + 內頁爬取
    max_pages: 想要爬幾頁 (建議先設 5 頁測試，正式報告可以設 10 或 20)
    """
    base_url = "https://ani.gamer.com.tw/animeList.php?sort=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    all_data = []

    for page in range(1, max_pages + 1):
        # 使用 console.print 可以印出有顏色的字
        console.print(f"[bold cyan]--- 正在爬取第 {page} 頁 ---[/bold cyan]")
        # sort=2 代表依人氣排序 (累積觀看數)，這樣比較容易抓到舊的神作
        url = f"{base_url}?sort=1&page={page}"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"第 {page} 頁連線失敗")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        anime_items = soup.find_all("a", class_="theme-list-main") 

        print(f"  > 本頁找到 {len(anime_items)} 部動畫，開始進入內頁抓評分...")

        for item in anime_items:
            title = item.find("p", class_="theme-name").text.strip()
            view_count_str = item.find("div", class_="show-view-number").find("p").text.strip()
            info_text = item.find("p", class_="theme-time").text.strip()
            
            # 取得內頁連結 (href)
            href = item.get('href')
            full_link = f"https://ani.gamer.com.tw/{href}"
            
            # 1. 處理觀看數
            if "萬" in view_count_str:
                view_count = int(float(view_count_str.replace("萬", "")) * 10000)
            elif view_count_str.isdigit():
                view_count = int(view_count_str)
            else:
                view_count = 0
                
            # 處理年份 (修正後)
            # 原始寫法: re.search(r'^\d{4}', info_text) -> 錯誤，因為開頭是中文
            year_match = re.search(r'\d{4}', info_text)  # ✅ 修正：拿掉 ^
            
            if year_match:
                year = int(year_match.group())
            else:
                # 為了除錯，建議這裡可以把抓不到的字印出來看看長怎樣
                print(f" [Debug] 抓不到年份，原始文字是: {info_text}") 
                year = "未知"

            # 處理題材
            is_isekai = "是" if ('異世界' in title or '轉生' in title) else "否"

            # 【進入內頁】同時抓評分 + 判斷狀態
            # 簡化輸出，讓畫面乾淨一點
            console.print(f"  > 分析: [yellow]{title}[/yellow] ({year})...", end="\r")
            
            # --- 修改：接收三個回傳值 (多了 tags_str) ---
            real_score, real_status, tags_str = get_anime_details(full_link, year)
            
            # 顯示結果給你看
            # print(f"      -> 判定為: {real_status}, 評分: {real_score}")

            all_data.append({
                "動畫名稱": title,
                "觀看次數": view_count,
                "年份": year,
                "狀態": real_status, # 使用新的時間判斷結果
                "是否異世界": is_isekai,
                "評分": real_score, # 這是真實的了！
                "主題標籤": tags_str  # 新增這一欄
            })
            
        # 每一頁爬完休息一下
        time.sleep(2)
    
    return all_data

# --- 【安全模式】保證顯示版 ---
def print_rich_table(df):
    """
    使用 Rich 模組繪製表格 (強制全青色/白色配色，避免黑底黑字問題)
    """
    # 1. 標題與邊框：強制標題為青色
    table = Table(
        title="[cyan]📊 巴哈姆特動畫瘋 - 爬蟲分析報告[/cyan]", 
        box=box.ROUNDED, 
        header_style="bold cyan",  # 表頭強制青色
        show_lines=True            # 顯示分隔線，看得更清楚
    )

    # 2. 設定欄位 (全部靠左或置中，不設 style 以免變黑)
    table.add_column("排名", justify="center")
    table.add_column("動畫名稱", justify="left", no_wrap=False, max_width=30, overflow="fold")
    table.add_column("年份", justify="center")
    table.add_column("狀態", justify="center")
    table.add_column("觀看數", justify="right")
    table.add_column("評分", justify="right")
    # --- 新增這欄 ---
    # max_width=20 加上 overflow="fold" 代表如果標籤太多，會自動換行顯示，不會切掉
    table.add_column("主題標籤", justify="left", style="magenta", max_width=20, overflow="fold")
    table.add_column("異世界", justify="center")

    # 3. 逐行加入資料 (全部強制加上顏色標籤)
    for index, row in df.iterrows():
        
        # 為了保險，所有欄位都加上 [white] 或 [cyan] 標籤
        # 如果你的背景是黑的，white 一定看得到
        
        rank_str = f"[white]{index + 1}[/]"
        name_str = f"[cyan]{row['動畫名稱']}[/]"  # 你原本看得到這個，所以繼續用青色
        year_str = f"[white]{row['年份']}[/]"
        
        # 狀態
        if row['狀態'] == "已完結":
            status_str = f"[bold red]{row['狀態']}[/]" # 紅色通常在黑底也很清楚
        else:
            status_str = f"[bold green]{row['狀態']}[/]"
        
        # 觀看數 (強制白色)
        view_str = f"[white]{row['觀看次數']/10000:.1f}萬[/]"

        # 評分 (強制白色，高分用黃色)
        if row['評分'] >= 9.5:
            score_str = f"[bold yellow]{row['評分']}[/]"
        else:
            score_str = f"[white]{row['評分']}[/]"

        # 處理主題標籤 
        # 檢查是否為空值 (NaN)，如果是就顯示 "-"
        raw_tags = row.get('主題標籤', '')
        if pd.isna(raw_tags) or raw_tags == "":
            tags_str = "-"
        else:
            # 將逗號換成空格，視覺上比較乾淨，或者保留逗號也可以
            # 這裡設定為紫色 (magenta)
            tags_str = f"[magenta]{raw_tags}[/]"
        
        # 異世界 (改成文字 YES/NO 避免亂碼)
        isekai_str = f"[white]{'YES' if row['是否異世界'] == '是' else '-'}[/]"

        # 加入 Row (記得順序要跟上面的 add_column 一樣)
        table.add_row(
            rank_str,
            name_str,
            year_str,
            status_str,
            view_str,
            score_str,
            tags_str, # 新增的變數放這裡
            isekai_str
        )

    console.print(table)

# --- 執行爬蟲並存檔 ---
if __name__ == "__main__":
    
    console.print("[bold green]🚀 爬蟲啟動中...[/bold green]")

    # 設定要爬幾頁？建議先設 5 頁試跑，確認沒問題後再改成 10 或 20 頁抓更多資料
    # 5 頁大約需要 2-3 分鐘 (因為要進內頁)
    data = get_anime_data_v3(max_pages=11) 
    
    df = pd.DataFrame(data)

    # 1. 存檔
    output_file = "anime_data.xlsx"
    df.to_excel(output_file, index=False)
    
    print("\n" + "="*50)
    
    # 2. 再呼叫 Rich 表格
    if not df.empty:
        df_sorted = df.sort_values(by="觀看次數", ascending=False).reset_index(drop=True)
        print_rich_table(df_sorted)
    else:
        console.print("[bold red]❌ 沒有抓到任何資料！[/bold red]")