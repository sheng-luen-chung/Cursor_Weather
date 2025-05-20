import requests
import os
from datetime import datetime

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
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city['q']}&appid={API_KEY}&units=metric&lang=zh_tw"
    )
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

    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=zh_tw"
    )
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
        temp_max = max(e['main']['temp_max'] for e in entries)
        temp_min = min(e['main']['temp_min'] for e in entries)
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

# 產生 HTML
update_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>自動更新天氣網頁</title>
    ...（後略，與原本相同）...'''

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
    </div>
'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
