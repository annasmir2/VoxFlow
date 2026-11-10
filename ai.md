# AI Implementation Notes

## AI model used
The project uses Ollama with the qwen3:8b model as the primary AI provider for reminder interpretation.

## Ollama integration
The backend AI route calls Ollama through the local HTTP API at http://localhost:11434 by default. The provider selection is controlled through environment values such as:

- AI_PROVIDER=ollama
- OLLAMA_BASE_URL=http://localhost:11434
- OLLAMA_MODEL=qwen3:8b

The AI flow is implemented in the backend service layer and is intentionally kept lightweight and validation-focused.

## Why Ollama
Ollama was chosen because it makes a local model easy to run without introducing external paid API dependencies. The project keeps the architecture simple while still giving the assistant a structured model-backed interpretation step for natural-language reminder creation.

## Voice recognition implementation
The frontend uses the browser’s native Web Speech API:

- SpeechRecognition or webkitSpeechRecognition for microphone capture
- English UK locale for the listening flow
- continuous recognition with safe restart logic after unexpected browser termination
- transcript display before submission

This keeps the microphone workflow local to the browser and avoids requiring a third-party speech vendor.

## AI reminder interpretation
The AI service parses reminder instructions into a structured payload containing:

- intent
- title
- remind_at
- requires_clarification
- clarification

The validation flow rejects incomplete or unclear reminders instead of inventing missing data. This is important for safety and for preserving a reliable reminder flow.

## AI-generated responses
After a reminder is created, the frontend shows an AI confirmation message and optionally speaks it using the browser speech synthesis API. This is used as a lightweight voice response layer for confirmations rather than for a full conversational system.

## AI-assisted development tools and usage
This project used local development tools and verification rather than a large AI-assisted workflow. The main AI-assisted work included:

- local parsing validation for reminder extraction
- structured response checking against the backend route
- verification of the Ollama provider path and model output
- targeted runtime checks for natural language and reminder creation

## What was manually reviewed and tested
The project was checked in the real environment for:

- Ollama availability and qwen3:8b model presence
- backend health and AI route response
- reminder creation from natural language
- backend regression test pass
- frontend production build pass

The project does not claim a large-scale AI assistant experience beyond the current reminder-focused flow.
