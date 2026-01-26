# Bossy Radar

Bossy Radar is a tool to track and analyze company data.

## Project Structure

- **backend/**: FastAPI + Typer + SQLModel (Managed by `uv`)
- **frontend/**: Nuxt 4 + Tailwind CSS

## Quick Start

### Backend

```bash
cd backend
uv run python cli.py hello [Name]
uv run uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```
