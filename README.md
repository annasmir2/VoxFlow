# VoxFlow

Voice-first productivity assistant for turning natural speech into actionable reminders and task tracking.

<p align="center">
  <img src="./Screenshot%202026-11-10%20at%2022.35.02.png" alt="VoxFlow dashboard UI" width="1200" />
</p>

## Overview

VoxFlow is a lightweight productivity dashboard that lets users speak naturally, convert that speech into structured reminders, and keep track of what needs attention next. The app blends browser-based voice capture, local AI interpretation, and reminder management into a single workflow designed for quick capture without manual typing.

## Features

- Voice input with browser speech recognition
- AI-powered reminder parsing from natural language prompts
- Task and reminder dashboard with live status tracking
- Browser notification support for upcoming reminders
- FastAPI backend + Next.js frontend architecture
- Local-first AI workflow using Ollama

## Tech stack

- Frontend: Next.js, React, TypeScript
- Backend: FastAPI, Python
- AI layer: Ollama with qwen3:8b
- Data: SQLite for local persistence
- UI: dark productivity dashboard with live status panels

## Project structure

- `backend/` — FastAPI API, database configuration, services, and reminder/task logic
- `frontend/` — Next.js dashboard and speech-driven UI
- `docs/` — architecture and project notes
- `tests/` — backend validation checks

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### AI model

This project is configured to use Ollama locally. Make sure Ollama is running and the model is available, for example:

```bash
ollama pull qwen3:8b
```

## Documentation

- [docs/project-introduction.md](docs/project-introduction.md)
- [docs/architecture.md](docs/architecture.md)
- [ai.md](ai.md)

## Summary

VoxFlow is built for the everyday workflow of capturing tasks quickly from spoken language and turning them into reliable reminders that are easy to manage from a single, focused dashboard.
