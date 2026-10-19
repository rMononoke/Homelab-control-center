---
trigger: always_on
---

---
description: Global architecture, tech stack, and code quality rules for Homelab Control Center
globs: *
alwaysApply: true
---

# Homelab Control Center — Global Project Rules

## 1. Project Overview & Goal
We are building **Homelab Control Center** — a microservices-based server management and monitoring platform (ChatOps Telegram Bot + Web Dashboard).
The ultimate DevOps goal for this repository is to write unit tests (`pytest`), package all components into a **Helm chart**, and deploy them to Kubernetes via a 4-stage **GitLab CI/CD** pipeline (`build`, `test`, `staging`, `prod`).

## 2. Monorepo Structure & Strict Isolation
- `services/agent/` — Python microservice interacting with the Linux host (`psutil`) and Docker daemon (`docker-py`).
- `services/core-api/` — Python microservice managing business logic, alerts, and PostgreSQL (`SQLAlchemy`).
- `services/bot/` — Python microservice running the Telegram bot (`aiogram 3.x`).
- `frontend/` — TypeScript + React + Vite + Tailwind CSS dashboard (evolving into a Telegram Mini App).
- `deploy/` — Docker Compose, Prometheus/Grafana configs, and future Helm charts.

**CRITICAL BOUNDARY RULE:**
- Never import Python modules across different services. Each service is an independent container.
- Communication chain:
  - `bot` -> HTTP (`httpx`) -> `core-api`
  - `frontend` -> HTTP (`fetch`/`axios`) -> `core-api`
  - `core-api` -> HTTP (`httpx`) -> `agent` AND `core-api` -> TCP (`asyncpg`) -> `postgres`

## 3. Python 3.12 & Framework Standards
- **Async-First:** Never block the asyncio event loop.
  - Forbidden: `requests`, `time.sleep()`.
  - Required: `httpx.AsyncClient`, `asyncio.sleep()`.
  - Wrap any synchronous I/O or CPU-bound calls (especially `docker-py` and heavy `psutil` calls) in `await asyncio.to_thread(...)`.
- **Pydantic v2 ONLY:** Use `model_dump()`, `model_validate()`, `ConfigDict`, and `pydantic-settings` (`SettingsConfigDict`). Never use v1 `.dict()` or `class Config`.
- **SQLAlchemy 2.0 Async ONLY:** Use `AsyncSession`, `select()`, `Mapped[]`, and `mapped_column()`. Never use legacy 1.x `session.query()`.
- **Aiogram 3.x ONLY:** Use `Router()`, magic filters (`F`), and `CallbackData` factories. Never use aiogram 2.x syntax (`executor`, `@dp.message_handler`).

## 4. TypeScript & React Standards
- Strict TypeScript: define explicit interfaces for all API payloads and props. Never use `any`.
- Read backend URLs exclusively via `import.meta.env.VITE_API_URL`.

## 5. DevOps & Cloud-Native Readiness (12-Factor App)
- **Zero Hardcode:** All secrets, tokens, DB URLs, and service hostnames must be loaded from environment variables.
- **Health & Metrics:** Every HTTP microservice (`agent`, `core-api`) must expose:
  - `GET /healthz` returning `{"status": "ok"}` (for Docker/K8s probes).
  - `GET /metrics` via `prometheus-fastapi-instrumentator`.
- **Dockerfiles:** Always use multi-stage builds (`python:3.12-slim` or `node:20-alpine` -> `nginx:alpine`), minimize layers, and run runtime containers as a non-root user (except `agent` where socket permissions require specific group mapping).
- **Testability:** Decouple business logic and data parsers from FastAPI route handlers so they can be easily covered with `pytest` unit tests.
