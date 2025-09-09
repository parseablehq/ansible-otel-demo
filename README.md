# Ansible + OpenTelemetry Demo

Minimal setup to collect Ansible playbook telemetry (traces and logs) via an OpenTelemetry Collector.

## Assets

- Collector config: [otel-config.yaml](./otel-config.yaml)
- Compose to run the Collector: [compose.yaml](./compose.yaml)
- Environment template: [env.example](./env.example)
- Ansible callback plugin: [ansible/callback_plugins/otel.py](./ansible/callback_plugins/otel.py)
- Ansible project scaffolding:
  - [ansible/ansible.cfg](./ansible/ansible.cfg)
  - [ansible/inventory.ini](./ansible/inventory.ini)
  - [ansible/site.yml](./ansible/site.yml)
  - [ansible/requirements.txt](./ansible/requirements.txt)

Repo paths for quick reference:

- `otel-config.yaml`
- `compose.yaml`
- `env.example`
- `ansible/callback_plugins/otel.py`
- `ansible/ansible.cfg`, `ansible/inventory.ini`, `ansible/site.yml`, `ansible/requirements.txt`

## Quick Start

1) Prepare environment
   - Copy `env.example` to `.env` and set Parseable endpoint, auth, and stream names as needed.
   - Optionally set `OTEL_SERVICE_NAME` to label telemetry from Ansible.

2) Start the OpenTelemetry Collector
   - `docker compose -f compose.yaml --env-file .env up -d`

3) Install Ansible + OpenTelemetry Python deps (for the callback plugin)
   - `python -m venv .venv && source .venv/bin/activate`
   - `pip install -r ansible/requirements.txt`

4) Run the sample playbook
   - `ansible-playbook -i ansible/inventory.ini ansible/site.yml`

The Collector listens on OTLP gRPC `:4317` and HTTP `:4318`. The Ansible callback plugin defaults to sending logs and traces to `http://localhost:4318/v1/logs` and `/v1/traces`. You can override via `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` and `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` if needed.
