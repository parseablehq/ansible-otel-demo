# Ansible + OpenTelemetry Demo

Minimal setup to collect Ansible playbook telemetry (traces and logs) via an OpenTelemetry Collector.

## Assets

- Collector config: [/blogs/static/ansible-otel-demo/otel-config.yaml](/blogs/static/ansible-otel-demo/otel-config.yaml)
- Compose to run the Collector: [/blogs/static/ansible-otel-demo/compose.yaml](/blogs/static/ansible-otel-demo/compose.yaml)
- Environment template: [/blogs/static/ansible-otel-demo/.env.example](/blogs/static/ansible-otel-demo/.env.example)
- Ansible callback plugin: [/blogs/static/ansible-otel-demo/ansible/callback_plugins/otel.py](/blogs/static/ansible-otel-demo/ansible/callback_plugins/otel.py)
- Ansible project scaffolding:
  - [/blogs/static/ansible-otel-demo/ansible/ansible.cfg](/blogs/static/ansible-otel-demo/ansible/ansible.cfg)
  - [/blogs/static/ansible-otel-demo/ansible/inventory.ini](/blogs/static/ansible-otel-demo/ansible/inventory.ini)
  - [/blogs/static/ansible-otel-demo/ansible/site.yml](/blogs/static/ansible-otel-demo/ansible/site.yml)
  - [/blogs/static/ansible-otel-demo/ansible/requirements.txt](/blogs/static/ansible-otel-demo/ansible/requirements.txt)

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

