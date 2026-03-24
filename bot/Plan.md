# SE Toolkit Bot Development Plan

## Overview

This document outlines the development plan for the SE Toolkit Telegram Bot, which provides students with access to lab information, scores, and AI-powered assistance through a conversational interface.

## Phase 1: Scaffold (Current Task)

- Create project structure with separation of concerns
- Implement testable handler architecture (handlers don't depend on Telegram)
- Add `--test` mode for offline verification without Telegram connection
- Set up dependency management with `pyproject.toml` and `uv`

## Phase 2: Backend Integration

- Implement LMS API client in `services/lms_client.py`
- Connect `/health`, `/labs`, `/scores` handlers to real backend
- Add error handling and retry logic for API calls
- Implement caching for frequently accessed data

## Phase 3: Intent Routing

- Add LLM client for natural language understanding
- Implement intent classification (command vs. question)
- Route messages to appropriate handlers based on intent
- Add context management for multi-turn conversations

## Phase 4: Deployment

- Create Docker configuration for bot service
- Set up health checks and monitoring
- Configure logging and error reporting
- Implement graceful shutdown and restart policies

## Architecture Principles

1. **Testability**: All handlers work without Telegram
2. **Separation**: Transport layer (Telegram) separate from business logic
3. **Configuration**: Environment-based configuration for different environments
4. **Error Handling**: Graceful degradation when services are unavailable
