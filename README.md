# ⚡ NeonPulse AI — Next-Gen AI Trading Terminal & Simulator

NeonPulse AI is a high-performance, simulated quantitative trading platform engineered for real-time market analysis, paper trading, and autonomous AI-assisted execution. It bridges the gap between algorithmic infrastructure and natural language control by pairing live streaming market data with an intelligent LLM Copilot capable of analyzing technical indicators and executing trades on your behalf.

Designed with a sleek, responsive Glassmorphic Dark UI featuring a signature 30% neon yellow accent, NeonPulse AI delivers a professional-grade financial terminal experience directly in the browser.

---

## 🌟 Core Features

- ⚡ **Real-Time Data Streaming:** Integrated directly with the Alpaca IEX Data Stream to ingest real-time ticks, snapshots, and price updates for top-tier equities (e.g., `AAPL`, `NVDA`, `TSLA`, `SPY`).
- 🤖 **Autonomous AI Trading Copilot:** Powered by the Groq LLM (`openai/gpt-oss-120b`), the Copilot calculates technical indicators (SMA-20, SMA-50, RSI) and translates natural language commands into executed market orders.
- 📊 **Interactive Market Visualization:** Features high-framerate candlestick charts built with `lightweight-charts` supporting customizable timeframes, trendlines, and dynamic auto-scaling.
- 💼 **Live Portfolio Heatmap:** Visualizes portfolio allocation and performance using `d3-hierarchy` treemaps, dynamically color-coded by unrealized P&L intensity.
- 🛡️ **Zero-Risk Paper Trading Environment:** Begin with a virtual $10,000 cash balance. Monitor Equity, Cash, and Unrealized P&L in real-time without risking real capital.
- 🎨 **Premium Glassmorphism Interface:** A modern, responsive layout constructed with Tailwind CSS, utilizing custom scrollbars and floating neon accent panels.

---

## 🏗️ System Architecture & Tech Stack

NeonPulse AI employs a decoupled, asynchronous architecture optimized for high-throughput data processing and low-latency UI rendering.

### **Frontend** (Next.js 14 App Router)
- **Language:** TypeScript
- **State Management:** Zustand
- **Styling:** Tailwind CSS (Custom glassmorphism & neon theming)
- **Data Visualization:** `lightweight-charts`, `d3-hierarchy`
- **Real-Time Communication:** Server-Sent Events (SSE) via `EventSource`

### **Backend** (FastAPI)
- **Language:** Async Python 3.12
- **Database:** SQLite via Async SQLAlchemy & Alembic (ORM)
- **Market Data Feeds:** Alpaca Market Data API v2 (Support for Mock & Polygon providers)
- **AI Engine:** Groq API (`openai/gpt-oss-120b`)
- **Package Management:** `uv`

<GenerateWidget component_placeholder_id="GenerateWidget_c_64305994987fa847_r_e9808d48db33cf37_0" height="600px" type="inline_visualization">
<skills>diagram</skills>

**Idea:** An interactive directory tree that visualizes the monorepo structure, allowing users to explore the separation between the Next.js frontend and FastAPI backend.
**Visual type:** Interactive Hierarchical Directory Tree
**Data specification:**
- **Data structure:** Hierarchical JSON representing directories and files.
- **Initial values:**
  - `TradingBot/`
    - `backend/`
      - `alembic/` (Database Migrations)
      - `app/`
        - `api/` (REST Endpoints)
        - `core/` (Config & DB Setup)
        - `models/` (SQLAlchemy Models)
        - `schemas/` (Pydantic Schemas)
        - `services/` (Trading Logic & AI)
      - `.env`
      - `pyproject.toml`
    - `frontend/`
      - `app/` (Next.js Router)
      - `components/` (UI Panels)
      - `hooks/` (SSE & State)
      - `stores/` (Zustand Stores)
      - `.env.local`
    - `docker-compose.yml`
    - `README.md`
- **Mapping:** Node hierarchy maps to folder structure. Leaf nodes represent files.
**User controls:** Click on folder nodes to expand/collapse their contents.
**Interactivity:** Hovering over specific directories (like `services/` or `components/`) reveals a tooltip explaining their architectural responsibility.
**Animation:** Smooth expand/collapse transitions.
</GenerateWidget>

---

## 🚀 Quickstart Guide

### Prerequisites
- **Node.js:** v18.x or higher
- **pnpm:** `npm install -g pnpm`
- **Python:** v3.12 or higher
- **uv:** `pip install uv`

### 1. Environment Configuration

Configure the required API keys before launching the platform.

**Backend Setup (`backend/.env`):**
```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./tradingbot.db

# Market Data Provider (alpaca for live, mock for offline)
MARKET_DATA_PROVIDER=alpaca
ALPACA_API_KEY=YOUR_ALPACA_KEY
ALPACA_API_SECRET=YOUR_ALPACA_SECRET
STALE_PRICE_SECONDS=30

# AI Copilot Configuration
GROQ_API_KEY=YOUR_GROQ_KEY
GROQ_MODEL=openai/gpt-oss-120b
COPILOT_MAX_TRADES_PER_REPLY=5
AI_AUTO_EXECUTE=true

# Initial Portfolio Configuration
STARTING_CASH=10000
CORS_ORIGINS=["*"]
# TradingBot
