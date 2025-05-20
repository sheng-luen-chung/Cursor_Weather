import requests
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY = os.getenv('OWM_API_KEY')
LOCAL_TZ = ZoneInfo("Asia/Taipei")

CITIES = [
    {"name": "台北市",    "q": "Taipei,tw"},
    {"name": "San Mateo", "q": "San Mateo,us"},
    {"name": "Chicago",   "q": "Chicago,us"}
]

# 用來存當前天氣與經緯度
city_coords = {}

# 1. 取得各城市當前天氣與座標
for city in CITIES:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city['q']}&appid={API_KEY}&units=metric&lang=zh_tw"
    )
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        city_coords[city['name']] = {
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
            "current": {
                "temp":  data["main"]["temp"],
                "desc":  data["weather"][0]["description"],
                "icon":  data["weather"][0]["icon"],
            }
        }
    else:
        city_coords[city["name"]] = {
            "lat": None,
            "lon": None,
            "current": {
                "temp": "N/A",
                "desc": "取得失敗",
                "icon": ""
            }
        }

# 2. 取得未來兩天預報
for city in CITIES:
    name = city["name"]
    lat  = city_coords[name]["lat"]
    lon  = city_coords[name]["lon"]

    if lat is None or lon is None:
        city_coords[name]["forecast"] = []
        continue

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={API_KEY}"
        f"&units=metric&lang=zh_tw"
    )
    resp = requests.get(url)
    data = resp.json() if resp.status_code == 200 else {}

    # 以台北時區的「今天」為基準
    today = datetime.now(LOCAL_TZ).date()

    # 收集明天、後天的所有時段資料
    forecast_days = {}
    for entry in data.get("list", []):
        # 先解成帶時區的 datetime，再轉到本地
        dt_utc   = datetime.fromtimestamp(entry["dt"], tz=ZoneInfo("UTC"))
        dt_local = dt_utc.astimezone(LOCAL_TZ)
        d = dt_local.date()

        if d == today:
            continue  # 跳過今天
        if d not in forecast_days:
            forecast_days[d] = []
        forecast_days[d].append(entry)
        if len(forecast_days) >= 2:
            break

    # 整理每天的最高／最低溫、描述與 icon
    forecast_list = []
    for i, (d, entries) in enumerate(list(forecast_days.items())[:2]):
        temps_max = [e["main"]["temp_max"] for e in entries]
        temps_min = [e["main"]["temp_min"] for e in entries]
        descs     = [e["weather"][0]["description"] for e in entries]
        icons     = [e["weather"][0]["icon"] for e in entries]

        forecast_list.append({
            "date":     d.strftime("%m/%d"),
            "temp_max": round(max(temps_max), 1),
            "temp_min": round(min(temps_min), 1),
            "desc":     max(set(descs), key=descs.count),
            "icon":     max(set(icons), key=icons.count),
            "label":    "明天" if i == 0 else "後天"
        })

    city_coords[name]["forecast"] = forecast_list

# 3. 以本地時區格式化最後更新時間
update_time = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M %Z")

# 4. 組 HTML 並寫入 index.html
html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自動更新天氣網頁</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1 {{
            margin-bottom: 1rem;
            font-size: 2.5rem;
        }}
        .weather-list {{
            display: flex;
            flex-direction: column;
            gap: 2rem;
            margin-top: 2rem;
        }}
        .weather-card {{
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            padding: 1.5rem 2rem;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            font-size: 1.2rem;
        }}
        .city-title {{
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }}
        .forecast-row {{
            display: flex;
            gap: 2rem;
            margin-top: 0.5rem;
        }}
        .forecast-block {{
            background: rgba(255,255,255,0.15);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            min-width: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .forecast-block img {{
            width: 48px;
            height: 48px;
        }}
        .update-time {{
            margin-top: 2rem;
            font-size: 1rem;
            color: #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>自動更新天氣網頁</h1>
        <div class="weather-list">
'''

for city in CITIES:
    name = city["name"]
    c = city_coords[name]
    html += f'''        <div class="weather-card">
            <div class="city-title">{name}</div>
            <div class="forecast-row">
                <div class="forecast-block">
                    <div>今日</div>
                    <div>{c["current"]["temp"]}°C</div>
                    <div>{c["current"]["desc"]}</div>
                    {"<img src=\"https://openweathermap.org/img/wn/" + c["current"]["icon"] + "@2x.png\" />" if c["current"]["icon"] else ""}
                </div>
'''
    for f in c["forecast"]:
        html += f'''                <div class="forecast-block">
                    <div>{f["label"]} ({f["date"]})</div>
                    <div>{f["temp_max"]}°C / {f["temp_min"]}°C</div>
                    <div>{f["desc"]}</div>
                    <img src="https://openweathermap.org/img/wn/{f["icon"]}@2x.png" alt="icon">
                </div>
'''
    html += '''            </div>
        </div>
'''

html += f'''        </div>
        <div class="update-time">最後更新時間：{update_time}</div>
    </div>
</body>
</html>'''

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
