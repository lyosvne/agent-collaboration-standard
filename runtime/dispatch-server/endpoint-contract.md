# Dispatch Server Runtime Contract

## Runtime

- Service: `pi-dispatch-server.service`
- Source: `/opt/pi-orchestrator/extensions/dispatch-server.py`
- Listen: `127.0.0.1:8765`
- Public proxy prefix: `/dispatch/`
- Runtime identity: `pi-dispatch:pi-dispatch`
- Dedicated environment file: `/opt/pi-orchestrator/config/dispatch.env`
- Canonical source: `runtime/dispatch-server/dispatch-server.py`

Environment values and authentication material are never stored in this
repository. The canonical unit uses `NoNewPrivileges`, a strict filesystem
sandbox, an empty capability bounding set, and journal logging.

## Public governance GET endpoints

- `/dispatch/roadmap`
- `/dispatch/north-star`
- `/dispatch/architecture`
- `/dispatch/fleet-division`
- `/dispatch/start-here`
- `/dispatch/truth/versions`

The versions response does not expose absolute ECS paths.

Caddy configuration was not recovered in this change. TLS, proxy routing,
access-log redaction, and rate limiting remain separately verifiable
production concerns; this contract does not claim that Caddy performs
application authentication.

## Authenticated runtime endpoints

- `GET /dispatch/all`
- `GET /dispatch/context`
- `GET /dispatch/fleet`
- `GET /dispatch/survey`
- `GET /dispatch/history/<agent>`
- `GET /dispatch/models`
- `GET /dispatch/health`
- `GET /dispatch/drift`
- `POST /dispatch/history/<agent>`

Authentication uses `X-Dispatch-Key` or `Authorization: Bearer <key>`. Query
string credentials are rejected to prevent access-log and browser-history
leakage. If `DISPATCH_KEY` is missing or empty, protected endpoints fail closed
with `503`.

`/dispatch/models` is protected because it can invoke an upstream API using the
production `QODER_PAT`. Upstream errors are sanitized, and results are cached
for the configured TTL.

## Response behavior

- Text endpoints use `text/plain; charset=utf-8`.
- JSON endpoints use `application/json; charset=utf-8`.
- Responses set `Cache-Control: no-cache`.
- Unknown endpoints return `404`.
- Missing or unreadable local context is represented in the response instead
  of terminating the process.
- Governance documents other than `/dispatch/roadmap` prefer the local mirror
  and use GitHub raw only as a read fallback. The roadmap endpoint retains its
  recovered legacy `DISPATCH_DIR/global-roadmap-v1.1.md` source until the
  manifest-aware G2 change.

## Recovery boundary

The first canonical source commit is byte-identical to the captured production
source. A later commit in the recovery PR hardens authentication and runtime
data exposure before deployment. Manifest-aware logical versions remain a
separate reviewed change.
