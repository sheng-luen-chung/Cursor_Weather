import requests
import os
from datetime import datetime

API_KEY = os.getenv('OWM_API_KEY')
CITIES = [
    {"name": "台北市", "q": "Taipei,tw"},
    {"name": "San Mateo", "q": "San Mateo,us"},
    {"name": "Chicago", "q": "Chicago,us"}
]

weather_data = []
for city in CITIES:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city['q']}&appid={API_KEY}&units=metric&lang=zh_tw"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        weather_data.append({
            "name": city["name"],
            "temp": data["main"]["temp"],
            "desc": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"]
        })
    else:
        weather_data.append({
            "name": city["name"],
            "temp": "N/A",
            "desc": "取得失敗",
            "icon": ""
        })

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
            gap: 1.5rem;
            margin-top: 2rem;
        }}
        .weather-card {{
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            padding: 1.5rem 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 2rem;
            font-size: 1.3rem;
        }}
        .weather-card img {{
            width: 60px;
            height: 60px;
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
for w in weather_data:
    html += f'''            <div class="weather-card">
                <div><b>{w['name']}</b></div>
                <div>{w['temp']}°C</div>
                <div>{w['desc']}</div>
                {f'<img src="https://openweathermap.org/img/wn/{w["icon"]}@2x.png" alt="icon">' if w['icon'] else ''}
            </div>\n'''
html += f'''        </div>
        <div class="update-time">最後更新時間：{update_time}</div>
    </div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html) 