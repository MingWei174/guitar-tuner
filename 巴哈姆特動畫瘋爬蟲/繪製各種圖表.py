import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d import Axes3D # 引入 3D 繪圖模組
from collections import Counter
from wordcloud import WordCloud

# --- 設定繪圖的中文字型 ---
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] 
plt.rcParams['axes.unicode_minus'] = False

# 1. 讀取 Excel 資料
print("正在讀取 Excel 檔案...")
try:
    df = pd.read_excel("anime_data.xlsx")
    # 確保年份被讀取為字串或數字，移除'未知'以便畫圖
    df = df[df['年份'] != "未知"]
    print(f"讀取成功，共 {len(df)} 筆資料")
except FileNotFoundError:
    print("找不到 anime_data.xlsx，請先執行 巴哈姆特動畫瘋爬蟲.py")
    exit()

# --- 新增分析：熱門標籤統計 ---

print("正在分析風格標籤...")

# 1. 資料前處理：把 "校園,喜劇" 這種字串拆開，變成一個巨大的 List
all_tags_list = []

# 遍歷每一行，忽略沒有標籤的資料 (dropna)
for tags_str in df['主題標籤'].dropna():
    if isinstance(tags_str, str) and tags_str.strip() != "":
        # 以逗號切割
        tags = tags_str.split(',')
        all_tags_list.extend(tags)

# 2. 計算頻率
tag_counts = Counter(all_tags_list)
# 轉成 DataFrame 方便繪圖
tag_df = pd.DataFrame(tag_counts.items(), columns=['標籤', '次數']).sort_values(by='次數', ascending=False)

print(f"共收集到 {len(all_tags_list)} 個標籤數據，包含 {len(tag_df)} 種不同標籤")

# --- 開始繪製 7 張圖表 ---

# 【圖表 1: Top 10 熱門動畫 (長條圖)】
plt.figure(figsize=(12, 6)) # 修改: 把圖表寬度從 10 加大到 12
top_10 = df.sort_values(by='觀看次數', ascending=False).head(10)
plt.barh(top_10['動畫名稱'], top_10['觀看次數'], color='skyblue')
plt.title("巴哈姆特動畫瘋-本月人氣排行 Top 10")
plt.xlabel("觀看次數")
plt.gca().invert_yaxis() # 讓第一名排在最上面

# 修改: 手動調整左邊界，避免超長標題被切掉
# left=0.4 代表左邊留 40% 的空間給文字 (因為那部 Lv9999 的標題太長了)
plt.subplots_adjust(left=0.45) 
plt.show()


#  【圖表 2: 本月最夯題材 Top 15 (橫向長條圖)】
plt.figure(figsize=(10, 8))
top_tags = tag_df.head(15).sort_values(by='次數', ascending=True) # 為了畫圖由上而下，先由小排到大

# 使用不同顏色凸顯
plt.barh(top_tags['標籤'], top_tags['次數'], color='#48C9B0')
plt.title("本月動漫作品 - 最熱門題材 Top 15")
plt.xlabel("出現次數")
plt.grid(axis='x', linestyle='--', alpha=0.5)

# 在柱狀圖旁標示數字
for i, v in enumerate(top_tags['次數']):
    plt.text(v + 1, i, str(v), va='center', fontsize=10)

plt.show()

#  【圖表 3: 主題標籤文字雲 (Word Cloud)】
# 文字雲需要字型路徑，否則中文會變亂碼
# Windows 常見路徑: C:\Windows\Fonts\msjh.ttc (微軟正黑體)
font_path = 'C:\\Windows\\Fonts\\msjh.ttc' 

try:
    wc = WordCloud(
        font_path=font_path, 
        width=1200, 
        height=800, 
        background_color="white",
        colormap="viridis", # 配色方案
        max_words=100
    )
    
    # generate_from_frequencies 吃的是字典格式 {'校園': 50, '戀愛': 30...}
    wc.generate_from_frequencies(tag_counts)

    plt.figure(figsize=(10, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off") # 關閉座標軸
    plt.title("動漫主題文字雲 (Tag WordCloud)", fontsize=15)
    plt.show()
    
except Exception as e:
    print(f"文字雲繪製失敗，可能是字型路徑錯誤: {e}")
    print("若在 Mac/Linux，請修改 font_path 為系統有的確切中文字型路徑")

# 【圖表 4: 異世界題材佔比 (圓餅圖)】
plt.figure(figsize=(6, 6))
genre_counts = df['是否異世界'].value_counts()
plt.pie(genre_counts, labels=genre_counts.index, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff'])
plt.title("熱門動畫題材結構分析：異世界與非異世界")
plt.show()


# --- 【圖表 5: 觀看數 vs 評分 (進階標註版)】 ---
plt.figure(figsize=(10, 6)) 
plt.scatter(df['觀看次數'], df['評分'], alpha=0.6, c='orange', s=50)

plt.title("動畫觀看數 vs 評分分佈圖 (四象限分析)")
plt.xlabel("觀看次數")
plt.ylabel("評分")
plt.grid(True, linestyle='--', alpha=0.5)

# X 軸格式化
def format_wan(x, pos):
    return f'{int(x/10000)}萬'
plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(format_wan))

# === 定義要標註的 4 個特殊點 ===
annotations = []

# 1. 人氣王 (觀看數最高)
top_view = df.loc[df['觀看次數'].idxmax()]
annotations.append({
    "data": top_view,
    "label": f"人氣王: {top_view['動畫名稱']}",
    "offset": (-20, 0), # 向左偏移
    "color": "red"
})

# 2. 叫座不叫好 (觀看數 > 前 25% 且 評分最低)
# 先算出觀看數的「前段班」門檻 (75百分位數)
high_view_threshold = df['觀看次數'].quantile(0.75)
# 在熱門片中找分數最低的
popular_low_score = df[df['觀看次數'] > high_view_threshold].sort_values(by='評分').iloc[0]
annotations.append({
    "data": popular_low_score,
    "label": f"爭議作: {popular_low_score['動畫名稱']}",
    "offset": (10, -20), # 向右下偏移
    "color": "green"
})

# 3. 冷門神作 (觀看數 < 平均值 且 評分最高)
# 找觀看數低於平均的
low_view_candidates = df[df['觀看次數'] < df['觀看次數'].mean()]
# 排序找分數最高的
hidden_gem = low_view_candidates.sort_values(by='評分', ascending=False).iloc[0]
annotations.append({
    "data": hidden_gem,
    "label": f"冷門神作: {hidden_gem['動畫名稱']}",
    "offset": (20, 20), # 向右上偏移
    "color": "purple"
})

# 4. 谷底 (評分最低)
# 直接找全體評分最低的
worst_score = df.loc[df['評分'].idxmin()]
annotations.append({
    "data": worst_score,
    "label": f"評分最低: {worst_score['動畫名稱']}",
    "offset": (10, 10), # 向右偏移
    "color": "black"
})

# === 統一執行標註 ===
for note in annotations:
    row = note['data']
    plt.annotate(
        text=note['label'], 
        xy=(row['觀看次數'], row['評分']), 
        xytext=note['offset'],  
        textcoords="offset points",
        ha='right' if note['offset'][0] < 0 else 'left', # 自動判斷文字要在點的左邊還是右邊
        va='center',
        fontsize=9, 
        fontweight='bold', 
        color=note['color'],
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color='gray') # 加個箭頭比較清楚
    )

plt.show()

# 【圖表 6: 年份熱度圖 (長條圖)】
plt.figure(figsize=(10, 5))
year_counts = df['年份'].value_counts().sort_index()
bars = plt.bar(year_counts.index.astype(str), year_counts.values, color='#76D7C4')
plt.title("排行榜中的動畫年份分佈 (神作之年?)")
plt.xlabel("年份")
plt.ylabel("上榜數量")
plt.bar_label(bars)
plt.grid(axis='y', linestyle='--', alpha=0.3)

# --- 關鍵修正 ---
# rotation=45: 文字逆時針旋轉 45 度
# fontsize=10: 字體設小一點點
# ha='right': 讓旋轉後的文字對齊刻度右邊，視覺比較整齊
plt.xticks(rotation=45, fontsize=10, ha='right') 

plt.tight_layout() # 自動調整邊界，避免旋轉後的文字被切掉
plt.show()

# 【圖表 7: 連載中 vs 已完結平均觀看數 (長條圖)】
plt.figure(figsize=(6, 6))
status_group = df.groupby('狀態')['觀看次數'].mean()
colors = ['#F1948A', '#85C1E9']
plt.bar(status_group.index, status_group.values, color=colors, width=0.5)
plt.title("連載中 vs 已完結 - 平均觀看熱度比較")
plt.ylabel("平均觀看次數")

# 這裡也要加上 '萬' 的單位標示比較直覺
for i, v in enumerate(status_group.values):
    plt.text(i, v + 1000, f"{int(v/10000)}萬", ha='center', fontweight='bold')

plt.show()


# 【圖表 8: 時序演進下的品質與熱度三維分佈 (3D 散佈圖)】
fig = plt.figure(figsize=(12, 9)) # 圖表加大一點，讓標題不擁擠
ax = fig.add_subplot(111, projection='3d')

# 準備資料
xs = df['年份']
ys = df['評分']
zs = df['觀看次數']

# 設定顏色：異世界題材用 "蕃茄紅"，非異世界用 "鋼藍色" (更專業的配色)
colors = df['是否異世界'].map({'是': '#E74C3C', '否': '#2980B9'})

# 設定點的大小：觀看次數越多，點越大
# 邏輯：(觀看數 / 10000) * 係數 + 基礎大小
sizes = (df['觀看次數'] / 10000) * 0.8 + 20 

# 繪製散佈圖 (加入 edgecolors 讓點有白邊，看起來較立體)
scatter = ax.scatter(xs, ys, zs, c=colors, s=sizes, alpha=0.7, edgecolors='white', linewidth=0.5)

# --- 修改重點 1: 專業標題 ---
ax.set_title("時序演進下的品質與熱度三維分佈\n(3D Analysis of Time, Quality, and Popularity)", fontsize=15, pad=20)

# --- 修改重點 2: 專業軸名稱 ---
ax.set_xlabel("發行年份 (Year)", fontsize=11, labelpad=10)
ax.set_ylabel("觀眾評分 (Rating)", fontsize=11, labelpad=10)
ax.set_zlabel("累積觀看數 (Views)", fontsize=11, labelpad=10)

# --- 修改重點 3: 強制調整 X 軸範圍 (解決 2025 消失問題) ---
# 找出資料中最大年份，然後 +2 年當作邊界，確保最右邊的點不會被切掉
max_year_in_data = df['年份'].max()
ax.set_xlim(df['年份'].min(), max_year_in_data + 1) 

# X 軸刻度強制設為整數 (避免出現 2024.5 這種怪年份)
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# Z 軸格式化 (顯示 '萬')
ax.zaxis.set_major_formatter(ticker.FuncFormatter(format_wan))

# 調整視角 (可以讓讀者更清楚看到年代的推進)
ax.view_init(elev=25, azim=-50)

# 加入圖例 (Legend) - 手動製作圖例以解釋顏色
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', label='異世界題材', markerfacecolor='#E74C3C', markersize=10),
    Line2D([0], [0], marker='o', color='w', label='非異世界', markerfacecolor='#2980B9', markersize=10)
]
ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 0.9))

plt.tight_layout()
plt.show()