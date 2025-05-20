# 自動更新網頁

這是一個使用 Flask 和 GitHub Actions 的自動更新網頁專案。網頁會每 10 分鐘自動更新一次。

## 功能特點

- 使用 Flask 框架建立網頁
- 每 10 分鐘自動更新內容
- 現代化的 UI 設計
- 使用 GitHub Actions 進行自動化部署

## 本地運行

1. 克隆專案：
```bash
git clone [你的專案URL]
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

3. 運行應用：
```bash
python app.py
```

## GitHub Actions 設置

專案已經配置了 GitHub Actions 工作流程，會自動每 10 分鐘更新一次。你可以在 `.github/workflows/update.yml` 中修改更新頻率。

## 技術棧

- Python 3.x
- Flask
- GitHub Actions
- HTML/CSS 