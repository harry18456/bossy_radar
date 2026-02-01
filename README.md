# Bossy Radar

Bossy Radar 是一個專門用來追蹤與分析公司資料的工具，提供勞動違規、財務狀況及公司治理等資訊。本專案旨在提升資訊透明度，協助求職者做出更明智的決定。

## 功能特色

- **公司搜尋**：透過名稱或統編輕鬆搜尋公司記錄。
- **違規追蹤**：查看歷史勞動法規違規紀錄。
- **財務分析**：存取財務摘要與薪資資訊（來源為公開資料）。
- **公司治理**：連結至官方利害關係人與治理資訊區。
- **響應式設計**：現代化且支援行動裝置的介面。

## 技術架構 (Tech Stack)

本專案採用現代化的技術堆疊，強調效能與開發者體驗。

### 後端 (Backend)

- **框架**：[FastAPI](https://fastapi.tiangolo.com/)
- **CLI 工具**：[Typer](https://typer.tiangolo.com/)
- **ORM**：[SQLModel](https://sqlmodel.tiangolo.com/)
- **套件管理**：[uv](https://github.com/astral-sh/uv)

### 前端 (Frontend)

- **框架**：[Nuxt 4](https://nuxt.com/) (Vue.js)
- **樣式**：[Tailwind CSS](https://tailwindcss.com/)

## 快速開始 (Quick Start)

### 前置需求 (Prerequisites)

- **Python**: 3.10+
- **Node.js**: 18+
- **uv**: 一個極速的 Python 套件安裝與解析器。

### 後端設定 (Backend Setup)

1. 進入後端目錄：

   ```bash
   cd backend
   ```

2. 安裝依賴套件：

   ```bash
   uv sync
   ```

3. 設定環境變數：
   複製 `.env.template` 為 `.env` 並填入所需數值。

   ```bash
   cp .env.template .env
   ```

4. 啟動開發伺服器：

   ```bash
   uv run uvicorn app.main:app --reload
   ```

5. 執行 CLI 指令（範例）：
   ```bash
   uv run python cli.py hello [Name]
   ```

### 前端設定 (Frontend Setup)

1. 進入前端目錄：

   ```bash
   cd frontend
   ```

2. 安裝依賴套件：

   ```bash
   npm install
   ```

3. 設定環境變數：
   複製 `.env.example` 為 `.env` 並進行相應設定。

   ```bash
   cp .env.example .env
   ```

4. 啟動開發伺服器：
   ```bash
   npm run dev
   ```

## 授權 (License)

本專案採用 [GNU Affero General Public License v3.0 (AGPL-3.0)](LICENSE) 授權。

AGPL-3.0 是一個 Copyleft 授權，要求任何修改程式碼並透過網路提供服務的人，都必須釋出其修改後的原始碼。這確保了專案能保持開放，並持續造福社群。
