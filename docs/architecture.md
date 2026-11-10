# VoxFlow AI Architecture

## High-level architecture
The system is split into three main layers:

1. Frontend dashboard
2. Backend API service
3. SQLite data layer

The frontend interacts with the backend through HTTP requests, while the backend stores task and reminder data in SQLite.

## Frontend layer
The frontend is a Next.js application that provides:

- dashboard views for tasks and reminders
- AI input panel for reminder creation
- browser microphone capture
- spoken assistant confirmation
- notification permission and reminder status updates

The major UI logic lives in the main app page component and is responsible for fetching reminders, creating tasks, and sending AI reminder requests.

## Backend layer
The backend is a FastAPI application that exposes routes for:

- health checks
- task CRUD operations
- reminder CRUD operations
- AI natural-language reminder creation

The service layer handles data validation and AI parsing, ensuring that prompt output is converted into a structured reminder before persistence.

## AI layer
The AI layer is intentionally narrow and pragmatic:

- it accepts natural-language reminder instructions
- it calls the configured AI provider
- it extracts and validates a structured reminder payload
- it creates the reminder only if the parsed values are valid

The default provider is Ollama using qwen3:8b, which runs locally without requiring a cloud API key.

## Data model
The application stores reminders and tasks in SQLite with the following primary features:

- task records for general activity tracking
- reminder records with title and scheduled time
- completion state and notification state metadata
- timestamps for creation and updates

## Notification flow
The reminder scheduler checks due reminders and marks them as active or notified according to the reminder rules. Browser notifications can be triggered from the client when permission is granted and the reminder becomes due.

## Security and reliability notes
- The project keeps local environment values in .env files and does not commit secret credentials.
- AI parsing is validated before persistence.
- The app avoids silently inventing reminder content when the AI response is incomplete or ambiguous.
- The prototype is built for local demo and testing use rather than multi-user production deployment.

## Why this architecture works
This design keeps the project straightforward:

- easy to run locally
- easy to debug
- easy to test
- fast to iterate on

It favors a practical engineering trade-off: a reliable reminder system with an AI-assisted natural-language layer, rather than a deep or highly abstract AI platform.
