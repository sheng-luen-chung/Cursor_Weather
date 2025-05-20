import requests
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY = os.getenv('OWM_API_KEY')

# 三個城市及其時區
CITIES = [
    {"name": "台北市",    "q": "Taipei,tw",       "tz": "Asia/Taipei"},
    {"name": "San Mateo", "q": "San Mateo,us",    "tz": "America/Los_Angeles"},
    {"name": "Chicago",   "q": "Chicago,us",      "tz": "America/Chicago"}
]

city_data = {}

# 1. 取得各城市當前天氣、時間與座標
for city in CITIES:
    name = city["name"]
    tz    = ZoneInfo(city["tz"])
    # 當前本地時間
    now_local = datetime.now(tz)
    time_str  = now_local.strftime("%H:%M")

    # 取得經緯度與當前天氣
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city['q']}&appid={API_KEY}&units=metric&lang=zh_tw"
    )
    resp = requests.get(url)
    if resp.status_code == 200:
        d = resp.json()
        city_data[name] = {
            "tz":       tz,
            "time":     time_str,
            "lat":      d["coord"]["lat"],
            "lon":      d["coord"]["lon"],
            "current": {
                "temp": d["main"]["temp"],
                "desc": d["weather"][0]["description"],
                "icon": d["weather"][0]["icon"]
            }
        }
    else:
        city_data[name] = {
            "tz":   tz,
            "time": time_str,
            "lat":  None, "lon": None,
            "current": {
                "temp": "N/A",
                "desc": "取得失敗",
                "icon": ""
            }
        }

# 2. 取得每個城市「接下來6小時」與「未來兩天」預報
for city in CITIES:
    name = city["name"]
    tz   = city_data[name]["tz"]
    lat  = city_data[name]["lat"]
    lon  = city_data[name]["lon"]

    if lat is None:
        city_data[name]["hourly"]   = []
        city_data[name]["forecast"] = []
        continue

    # 取得三小時一筆的 5 天預報
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={API_KEY}"
        f"&units=metric&lang=zh_tw"
    )
    resp = requests.get(url)
    data = resp.json() if resp.status_code == 200 else {}

    now_local = datetime.now(tz)
    end6h     = now_local + timedelta(hours=6)
    today     = now_local.date()

    # 收集接下來 6 小時內的時段
    hourly = []
    for entry in data.get("list", []):
        dt_utc   = datetime.fromtimestamp(entry["dt"], tz=ZoneInfo("UTC"))
        dt_local = dt_utc.astimezone(tz)
        if now_local < dt_local <= end6h:
            hourly.append({
                "time": dt_local.strftime("%H:%M"),
                "temp": round(entry["main"]["temp"], 1),
                "desc": entry["weather"][0]["description"],
                "icon": entry["weather"][0]["icon"]
            })
    city_data[name]["hourly"] = hourly

    # 收集明天、後天的所有三小時時段
    forecast_days = {}
    for entry in data.get("list", []):
        dt_utc   = datetime.fromtimestamp(entry["dt"], tz=ZoneInfo("UTC"))
        dt_local = dt_utc.astimezone(tz)
        d = dt_local.date()
        if d == today:
            continue
        forecast_days.setdefault(d, []).append(entry)
        if len(forecast_days) >= 2:
            break

    # 計算未來兩天的最高／最低溫等
    fc = []
    for i, (d, entries) in enumerate(list(forecast_days.items())[:2]):
        temps_max = [e["main"]["temp_max"] for e in entries]
        temps_min = [e["main"]["temp_min"] for e in entries]
        descs     = [e["weather"][0]["description"] for e in entries]
        icons     = [e["weather"][0]["icon"] for e in entries]

        fc.append({
            "label":    "明天" if i == 0 else "後天",
            "date":     d.strftime("%m/%d"),
            "temp_max": round(max(temps_max), 1),
            "temp_min": round(min(temps_min), 1),
            "desc":     max(set(descs), key=descs.count),
            "icon":     max(set(icons), key=icons.count)
        })
    city_data[name]["forecast"] = fc

# 3. 最後更新時間（以台北時間顯示即可）
update_time = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M （台北時間）")

# 4. 組 HTML
html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>自動更新天氣網頁</title>
<style>
  body {{ font-family:'Arial',sans-serif; margin:0; padding:0;
         display:flex; justify-content:center; align-items:center; min-height:100vh;
         background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white }}
  .container {{ text-align:center; padding:2rem;
                background:rgba(255,255,255,0.1); border-radius:15px; backdrop-filter:blur(10px);
                box-shadow:0 8px 32px 0 rgba(31,38,135,0.37) }}
  h1 {{ font-size:2.5rem; margin-bottom:1rem }}
  .weather-list {{ display:flex; flex-direction:column; gap:2rem; margin-top:2rem }}
  .weather-card {{ background:rgba(255,255,255,0.2); border-radius:10px; padding:1.5rem 2rem;
                   display:flex; flex-direction:column; align-items:flex-start; font-size:1.2rem }}
  .city-title {{ font-size:1.5rem; font-weight:bold; margin-bottom:0.5rem }}
  .hourly-row, .forecast-row {{ display:flex; gap:1rem; margin-top:0.5rem; flex-wrap:wrap }}
  .forecast-block {{ background:rgba(255,255,255,0.15); border-radius:8px;
                     padding:1rem 1.5rem; min-width:100px; display:flex;
                     flex-direction:column; align-items:center }}
  .forecast-block img {{ width:48px; height:48px }}
  .update-time {{ margin-top:2rem; font-size:1rem; color:#e0e0e0 }}
</style>
</head>
<body>
  <div class="container">
    <h1>自動更新天氣網頁</h1>
    <div class="weather-list">
'''

for city in CITIES:
    name = city["name"]
    cd   = city_data[name]
    html += f'''      <div class="weather-card">
        <div class="city-title">{name} {cd["time"]}</div>
        <!-- 接下來 6 小時預報 -->
        <div class="hourly-row">
'''
    for h in cd["hourly"]:
        html += f'''          <div class="forecast-block">
            <div>{h["time"]}</div>
            <div>{h["temp"]}°C</div>
            <div>{h["desc"]}</div>
            <img src="https://openweathermap.org/img/wn/{h["icon"]}@2x.png" alt="">
          </div>
'''
    html += '''        </div>
        <!-- 未來兩天預報 -->
        <div class="forecast-row">
          <div class="forecast-block">
            <div>今日</div>
            <div>{temp}°C</div>
            <div>{desc}</div>
            {icon}
          </div>
'''.format(
        temp=cd["current"]["temp"],
        desc=cd["current"]["desc"],
        icon=(f'<img src="https://openweathermap.org/img/wn/{cd["current"]["icon"]}@2x.png" alt="">'
               if cd["current"]["icon"] else "")
    )
    for f in cd["forecast"]:
        html += f'''          <div class="forecast-block">
            <div>{f["label"]} ({f["date"]})</div>
            <div>{f["temp_max"]}°C / {f["temp_min"]}°C</div>
            <div>{f["desc"]}</div>
            <img src="https://openweathermap.org/img/wn/{f["icon"]}@2x.png" alt="">
          </div>
'''
    html += '''        </div>
      </div>
'''

html += f'''    </div>
    <div class="update-time">最後更新時間：{update_time}</div>
  </div>
</body>
</html>
'''

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
