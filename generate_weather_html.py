import requests
import os
from datetime import datetime, timedelta

API_KEY = os.getenv('OWM_API_KEY')
CITIES = [
    {"name": "台北市", "q": "Taipei,tw", "lat": 25.04, "lon": 121.53},
    {"name": "San Mateo", "q": "San Mateo,us", "lat": 37.5630, "lon": -122.3255},
    {"name": "Chicago", "q": "Chicago,us", "lat": 41.8781, "lon": -87.6298}
]

# 月相對照表
MOON_PHASES = [
    (0.02, "新月", "🌑"),
    (0.23, "蛾眉月", "🌒"),
    (0.27, "上弦月", "🌓"),
    (0.48, "盈凸月", "🌔"),
    (0.52, "滿月", "🌕"),
    (0.73, "虧凸月", "🌖"),
    (0.77, "下弦月", "🌗"),
    (1.00, "殘月", "🌘")
]
def moon_phase_name(val):
    for threshold, name, emoji in MOON_PHASES:
        if val <= threshold:
            return name, emoji
    return "新月", "🌑"

# 取得城市的經緯度與天氣
city_coords = {}
for city in CITIES:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city['q']}&appid={API_KEY}&units=metric&lang=zh_tw"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        city_coords[city['name']] = {
            'lat': data['coord']['lat'],
            'lon': data['coord']['lon'],
            'current': {
                'temp': data['main']['temp'],
                'desc': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            }
        }
    else:
        city_coords[city['name']] = {
            'lat': city['lat'],
            'lon': city['lon'],
            'current': {
                'temp': 'N/A',
                'desc': '取得失敗',
                'icon': ''
            }
        }

# 取得未來兩天預報
for city in CITIES:
    name = city['name']
    lat = city_coords[name]['lat']
    lon = city_coords[name]['lon']
    if lat is None or lon is None:
        city_coords[name]['forecast'] = []
        continue
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=zh_tw"
    resp = requests.get(url)
    if resp.status_code != 200:
        city_coords[name]['forecast'] = []
        continue
    data = resp.json()
    today = datetime.utcnow().date()
    forecast_days = {}
    for entry in data['list']:
        dt = datetime.utcfromtimestamp(entry['dt'])
        date = dt.date()
        if date == today:
            continue
        if date not in forecast_days:
            forecast_days[date] = []
        forecast_days[date].append(entry)
        if len(forecast_days) >= 2:
            break
    forecast_list = []
    for date, entries in list(forecast_days.items())[:2]:
        temp_max = max([e['main']['temp_max'] for e in entries])
        temp_min = min([e['main']['temp_min'] for e in entries])
        descs = [e['weather'][0]['description'] for e in entries]
        icons = [e['weather'][0]['icon'] for e in entries]
        desc = max(set(descs), key=descs.count)
        icon = max(set(icons), key=icons.count)
        forecast_list.append({
            'date': date.strftime('%m/%d'),
            'temp_max': round(temp_max, 1),
            'temp_min': round(temp_min, 1),
            'desc': desc,
            'icon': icon
        })
    city_coords[name]['forecast'] = forecast_list

# 取得今日月相
for city in CITIES:
    name = city['name']
    lat = city_coords[name]['lat']
    lon = city_coords[name]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=moon_phase&timezone=Asia/Taipei"
    resp = requests.get(url)
    print(f"{name} moon API status: {resp.status_code}, url: {url}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"{name} moon API data: {data}")
        moon_val = data['daily']['moon_phase'][0]
        moon_name, moon_emoji = moon_phase_name(moon_val)
        city_coords[name]['moon'] = {'name': moon_name, 'emoji': moon_emoji}
    else:
        print(f"{name} moon API failed!")
        city_coords[name]['moon'] = {'name': '取得失敗', 'emoji': ''}

update_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

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
        .moon-phase {{
            margin-top: 1rem;
            font-size: 1.1rem;
            color: #ffe082;
            display: flex;
            align-items: center;
            gap: 0.5rem;
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
    name = city['name']
    c = city_coords[name]
    html += f'''<div class="weather-card">
        <div class="city-title">{name}</div>
        <div class="forecast-row">
            <div class="forecast-block">
                <div>今日</div>
                <div>{c['current']['temp']}°C</div>
                <div>{c['current']['desc']}</div>
                {f'<img src="https://openweathermap.org/img/wn/{c["current"]["icon"]}@2x.png" alt="icon">' if c['current']['icon'] else ''}
            </div>
'''
    for i, f in enumerate(c['forecast']):
        label = '明天' if i == 0 else '後天'
        html += f'''            <div class="forecast-block">
                <div>{label} ({f['date']})</div>
                <div>{f['temp_max']}°C / {f['temp_min']}°C</div>
                <div>{f['desc']}</div>
                <img src="https://openweathermap.org/img/wn/{f['icon']}@2x.png" alt="icon">
            </div>
'''
    html += f'''        </div>
        <div class="moon-phase">月相：{c['moon']['name']} {c['moon']['emoji']}</div>
    </div>
'''
html += f'''        </div>
        <div class="update-time">最後更新時間：{update_time}</div>
    </div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html) 