# Anthony Portfolio — Backend

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" /> <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" /> <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white" /> <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" /> <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" /> <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=websocket&logoColor=white" /> <img src="https://img.shields.io/badge/Poetry-60A5FA?style=for-the-badge&logo=poetry&logoColor=white" />

個人作品集網站的後端 API 服務，提供作品集管理、報價系統、即時聊天、案件管理等功能。

The backend API service for a personal portfolio website, providing portfolio management, quoting system, real-time chat, and case management features.

## 功能 Features

- **作品集管理 Portfolio Management** — CRUD 操作，支援圖片上傳至 Supabase Storage / CRUD operations with image uploads to Supabase Storage
- **服務項目管理 Service Management** — 服務分類與定價 / Service categorization and pricing
- **報價系統 Quoting System** — 客戶報價單，自動生成編號（QT-YYYYMMDD-NNN），寄送確認信 / Client quotes with auto-generated numbers and confirmation emails
- **即時聊天 Real-time Chat** — WebSocket 雙向通訊，支援圖片訊息、報價提案、已讀回執 / WebSocket bidirectional communication with image messages, quote offers, and read receipts
- **案件管理 Case Management** — 從報價成立案件，自動生成編號（CS-YYYYMMDD-NNN），結案需密碼驗證 / Create cases from quotes with auto-generated numbers, password-protected case closure
- **標籤與分類 Tags & Categories** — 模糊搜尋選擇器 / Fuzzy search selectors
- **關於頁面 About Page** — Markdown 編輯，自動儲存 / Markdown editing with auto-save
- **管理員驗證 Admin Auth** — JWT 認證，密碼保護敏感操作 / JWT authentication with password-protected sensitive operations
- **郵件通知 Email Notifications** — Gmail SMTP 寄送報價確認與案件成立通知 / Quote confirmation and case creation notifications via Gmail SMTP

## 技術架構 Tech Stack

| 類別 Category | 技術 Technology |
|---|---|
| 語言 Language | Python 3.12 |
| 框架 Framework | FastAPI |
| 資料庫 Database | PostgreSQL（Supabase） |
| ORM | SQLAlchemy 2.0 + asyncpg |
| 驗證 Auth | PyJWT |
| 即時通訊 Real-time | WebSocket |
| 檔案儲存 Storage | Supabase Storage |
| 郵件 Email | aiosmtplib + Gmail SMTP |
| 套件管理 Package Manager | Poetry |
| 設定管理 Config | pydantic-settings + dotenv |

## 專案結構 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI 應用程式入口 / App entry point
│   ├── config.py             # 環境變數設定 / Environment config
│   ├── database.py           # 資料庫連線與初始化 / DB connection & init
│   ├── models.py             # SQLAlchemy ORM 模型 / ORM models
│   ├── schemas.py            # Pydantic 驗證結構 / Pydantic schemas
│   ├── email_service.py      # 郵件寄送服務 / Email service
│   ├── routers/
│   │   ├── auth.py           # 管理員登入 / Admin login
│   │   ├── portfolios.py     # 作品集 CRUD / Portfolio CRUD
│   │   ├── services.py       # 服務項目 CRUD / Service CRUD
│   │   ├── quotes.py         # 報價管理 / Quote management
│   │   ├── cases.py          # 案件管理 / Case management
│   │   ├── chat.py           # 聊天室 WebSocket / Chat WebSocket
│   │   ├── tags.py           # 標籤管理 / Tag management
│   │   ├── categories.py     # 分類管理 / Category management
│   │   └── about.py          # 關於頁面 / About page
│   └── services/
│       └── storage.py        # Supabase Storage 服務 / Storage service
├── pyproject.toml
├── poetry.lock
├── Makefile
├── .env.example
└── .gitignore
```

## 快速開始 Getting Started

```bash
# 安裝依賴 Install dependencies
poetry install

# 複製環境變數 Copy environment variables
cp .env.example .env
# 編輯 .env 填入實際值 Edit .env with actual values

# 啟動開發伺服器 Start dev server
make dev
# 或 or
poetry run uvicorn app.main:app --reload --port 8000
```

## 環境變數 Environment Variables

參考 `.env.example` 設定以下變數 / Refer to `.env.example` for the following variables:

| 變數 Variable | 說明 Description |
|---|---|
| `DATABASE_URL` | PostgreSQL 連線字串 / Connection string |
| `SUPABASE_URL` | Supabase 專案網址 / Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 服務金鑰 / Service role key |
| `SMTP_HOST` | SMTP 主機 / SMTP host |
| `SMTP_PORT` | SMTP 連接埠 / SMTP port |
| `SMTP_USER` | SMTP 使用者 / SMTP user |
| `SMTP_PASSWORD` | SMTP 密碼 / SMTP password |
| `SMTP_FROM` | 寄件人信箱 / Sender email |
| `ADMIN_USERNAME` | 管理員帳號 / Admin username |
| `ADMIN_PASSWORD` | 管理員密碼 / Admin password |
| `JWT_SECRET` | JWT 簽章密鑰 / JWT signing secret |

## API 端點 API Endpoints

| 方法 Method | 路徑 Path | 說明 Description |
|---|---|---|
| `POST` | `/api/auth/login` | 管理員登入 / Admin login |
| `GET` | `/api/portfolios` | 取得作品集列表 / List portfolios |
| `POST` | `/api/portfolios` | 新增作品集 / Create portfolio |
| `GET` | `/api/services` | 取得服務列表 / List services |
| `POST` | `/api/quotes` | 建立報價單 / Create quote |
| `POST` | `/api/quotes/{id}/delete` | 刪除報價（需密碼）/ Delete quote (password required) |
| `GET` | `/api/cases` | 取得案件列表 / List cases |
| `POST` | `/api/cases` | 成立案件 / Create case |
| `POST` | `/api/cases/{id}/close` | 結案（需密碼）/ Close case (password required) |
| `WS` | `/api/chat/ws/{room_id}` | 聊天室 WebSocket / Chat WebSocket |
| `GET` | `/api/chat/rooms` | 取得聊天室列表 / List chat rooms |

## 授權 License

© 2026 Anthony Sung. All rights reserved.
