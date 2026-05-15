# SMARTX X-BRIDGE 

## Overview

SMARTX X-BRIDGE is a high-performance RFID device management platform built with FastAPI. It acts as middleware between physical RFID readers and business systems, providing real-time tag processing, multi-device management, flexible integrations, and a built-in web interface.

---

## Features

- **Multi-device RFID management** — Connect and manage multiple readers simultaneously via TCP/IP, Serial, or USB
- **Real-time tag processing** — Duplicate filtering, EPC/TID validation, RSSI monitoring, antenna and power control
- **Tag prefix filtering** — Accept only tags matching configured prefixes
- **Integrations** — Webhook with retry, MQTT (IoT), XTRACK, and relational database persistence (SQLite, MySQL, PostgreSQL)
- **Web interface** — Responsive dashboard with live updates, log viewer, and device settings
- **API** — Full RESTful API with interactive Swagger documentation
- **Simulation** — Simulate tags and events without physical hardware, including GTIN-14 generation
- **License management** — Built-in license validation
- **System tray** — Native tray icon integration
- **Prometheus metrics** — Built-in observability endpoint

---

## Project Structure

```
app/
├── async_func/       Background tasks (RFID polling, etc.)
├── core/             App factory, config, middlewares, exception handlers
├── db/               Database session and initialization
├── models/           SQLAlchemy models (Tag, Event)
├── routers/
│   ├── api/v1/       REST API endpoints
│   └── pages/        Web interface routes (dashboard, logs, settings)
├── schemas/          Pydantic schemas for validation
├── services/
│   ├── rfid/         RFID controller, event handling, integrations
│   ├── settings_service/  Dynamic config management
│   ├── license/      License validation
│   └── tray/         System tray integration
├── static/           Frontend assets (CSS, JS, images, sounds)
└── templates/        Jinja2 templates

config/
├── config.json       Main application configuration
└── devices/          Per-device RFID reader configuration files

alembic/              Database migration scripts
scripts/              Utility scripts (build, format, migrate, startup)
tests/                Unit and integration tests
docs/                 API documentation assets
```

---

## Configuration

### `config/config.json`

| Field                     | Type        | Default    | Description                                        |
| ------------------------- | ----------- | ---------- | -------------------------------------------------- |
| `TITLE`                   | string      | `"SMARTX"` | Application title                                  |
| `PORT`                    | int         | `5000`     | HTTP server port                                   |
| `LOG_PATH`                | string      | `"Logs"`   | Directory for log files                            |
| `DATABASE_URL`            | string      | `null`     | SQLAlchemy DB URL (SQLite/MySQL/PostgreSQL)        |
| `WEBHOOK_URL`             | string      | `null`     | Webhook endpoint for tag events                    |
| `XTRACK_URL`              | string      | `null`     | XTRACK integration URL                             |
| `TAG_PREFIX`              | string/list | `null`     | Accept only tags with this prefix (single or list) |
| `STORAGE_DAYS`            | int         | `7`        | Days to retain tag/event records                   |
| `CLEAR_OLD_TAGS_INTERVAL` | int         | `null`     | Seconds between automatic tag memory clears        |
| `ALWAYS_SEND`             | bool        | `false`    | Forward all tags to integrations, even duplicates  |
| `BEEP`                    | bool        | `false`    | Play beep sound on new tag read                    |
| `OPEN_BROWSER`            | bool        | `true`     | Auto-open browser on startup                       |

### `config/devices/*.json`

Each file defines one RFID reader (protocol, antennas, read power, events, etc). See `examples/devices/` for templates covering TCP, Serial, X714, R700, XPAD, ACUPAD, and SATO readers.

---

## Installation & Running

```bash
# Install dependencies
poetry install

# Run the application
poetry run python main.py

# Build standalone executable
poetry run python scripts/build_exe.py

# Run database migrations
poetry run python scripts/migrate.py

# Run tests
poetry run pytest
```

---

## API Groups

| Group           | Prefix                | Description                                                     |
| --------------- | --------------------- | --------------------------------------------------------------- |
| **RFID**        | `/api/v1/rfid`        | Read tags, EPCs, TIDs, GTIN stats, clear tag memory, write EPC  |
| **Devices**     | `/api/v1/devices`     | List devices, get/set config, device status and info            |
| **Application** | `/api/v1/application` | App settings CRUD, device config CRUD, restart/shutdown         |
| **Simulator**   | `/api/v1/simulator`   | Simulate tags, events, tag lists, GTIN-14 tag generation        |
| **Receive**     | `/api/v1/receive`     | Ingest tag/event data from external readers (X714, R700, XSCAN) |
| **License**     | `/api/v1/license`     | Get license info, upload license                                |
| **Controller**  | `/api/v1/controller`  | RFID controller runtime info                                    |

Full interactive documentation available at `/docs`.

---

## Tech Stack

| Layer           | Technology                        |
| --------------- | --------------------------------- |
| Runtime         | Python ≥3.11                      |
| Package manager | Poetry                            |
| Web framework   | FastAPI + Uvicorn                 |
| Database ORM    | SQLAlchemy + Alembic              |
| Templates       | Jinja2                            |
| RFID layer      | smartx-rfid                       |
| MQTT            | gmqtt                             |
| Metrics         | prometheus-fastapi-instrumentator |
| Auth            | passlib[bcrypt] + itsdangerous    |
| Tray            | pystray + Pillow                  |
| Audio           | pygame                            |
| Linter          | Ruff                              |
| Testing         | Pytest                            |
| Build           | PyInstaller                       |
