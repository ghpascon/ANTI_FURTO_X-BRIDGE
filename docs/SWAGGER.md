<img src="/static/images/logo.png" alt="Logo" class="img-fluid" style="height: 50px;" />

# SMARTX X-BRIDGE

[**HOME**](/) | [**LOGS**](/logs) | [**API DOCS**](/docs)

**SMARTX X-BRIDGE** is a professional RFID device management platform focused on high performance, real-time monitoring, and seamless integration with business systems.

---

## How It Works

X-BRIDGE acts as middleware between physical RFID readers and your management systems. It connects to one or more readers, processes incoming tag data in real time, applies filtering and validation rules, and forwards events to configured integrations.

**Data flow:**

1. **Configuration** — Define devices and application parameters
2. **Connection** — Automatic connection and reconnection to readers
3. **Processing** — Real-time tag capture, duplicate filtering, and EPC/TID validation
4. **Storage** — Persistent records with configurable retention policy
5. **Integration** — Forward data to webhook endpoints, MQTT broker, XTRACK, or external database
6. **Monitoring** — Structured logs, Prometheus metrics, and live web dashboard

---

## API Groups

### RFID — `/api/v1/rfid`

Read and query tag data from memory. Retrieve full tag objects, EPCs, TIDs, GTIN statistics, and tag counts. Supports clearing in-memory tag lists per device or globally, and writing new EPCs directly to tags.

### Devices — `/api/v1/devices`

List and inspect all registered RFID readers. Retrieve individual device configuration, current status, connection info, and supported device type templates.

### Application — `/api/v1/application`

Manage runtime application settings and device configuration files. Supports full CRUD for device configs, reading and updating global settings, checking for unsaved changes, and triggering restart or shutdown.

### Simulator — `/api/v1/simulator`

Inject synthetic tag and event data without physical hardware. Supports single tags, batches, generic events, and GTIN-14 tag generation — useful for development, testing, and demos.

### Receive — `/api/v1/receive`

Ingest tag and event data pushed by external readers or integrations. Supports generic tag/event payloads as well as device-specific formats (X714, R700, XSCAN).

### License — `/api/v1/license`

Retrieve current license information and upload a new license string.

### Controller — `/api/v1/controller`

Expose runtime information about the active RFID controller instance.

---

## Integration Options

- **Webhook** — HTTP POST to a configured URL on every new tag event, with automatic retry
- **XTRACK** — Send data directly to a SMARTX XTRACK server
- **Database** — Persist all tags and events to SQLite, MySQL, or PostgreSQL via SQLAlchemy

---

## Testing & Simulation

The Simulator group lets you validate your full integration pipeline without any RFID hardware:

- Inject individual tags or bulk lists
- Simulate GPI/GPO events and custom event payloads
- Generate valid GTIN-14 EPC codes for barcode-to-RFID workflows
- Run load tests with large tag volumes
