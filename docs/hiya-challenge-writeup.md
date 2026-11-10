# Hiya Challenge Write-up

## Project concept
VoxFlow AI is a voice-first personal reminder assistant designed to turn everyday spoken instructions into actionable reminders. The goal is to reduce friction for reminder creation while keeping the app simple, local, and reliable.

## Why it fits the challenge
The project matches the challenge themes by combining a real user-facing workflow with a practical AI layer and a browser-based voice interface. It is not just a static dashboard; it is a working reminder assistant that can interpret spoken or written reminder requests and store them for follow-up.

## What was built
- Dashboard for tasks and reminders
- Reminder CRUD workflow
- AI reminder creation using natural-language input
- Browser microphone capture for spoken entries
- Browser spoken confirmation through speech synthesis
- Local AI inference via Ollama
- SQLite storage for persistence

## What makes it strong
The system keeps the working reminder logic intact while layering AI and voice features on top. This makes the prototype feel like a usable personal assistant while preserving stability and real data handling. The backend validates AI responses before creating a reminder, which reduces malformed reminder creation.

## What is intentionally scoped
This is a focused prototype rather than a full enterprise assistant. It prioritizes reliability and functioning reminder capture over broad automation, multi-user orchestration, or advanced recurring scheduling.

## Verification performed
The project was validated with real runtime checks, including:

- backend health checks
- AI route verification
- natural-language reminder creation through Ollama
- backend pytest pass
- frontend production build pass

## Outcome
The result is a functioning prototype that demonstrates a practical voice and AI reminder workflow in a browser app and local backend environment.
