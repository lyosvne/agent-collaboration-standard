# Dispatch Server Deployment Prerequisites

This document defines preflight requirements only. It does not authorize or
perform deployment.

## Identity and files

- Create the system identity `pi-dispatch:pi-dispatch` with no login shell.
- Install the canonical Python source as `root:root`, mode `0644`.
- Keep source directories traversable but not writable by `pi-dispatch`.
- Create `/opt/pi/dispatch` as `pi-dispatch:pi-dispatch`, mode `0750`.
- Keep the governance mirror and drift report readable by `pi-dispatch`.
- Create `/opt/pi-orchestrator/config/dispatch.env` as
  `root:pi-dispatch`, mode `0640`.

The dedicated environment file may contain only variables required by this
service. It must not reuse the shared orchestrator environment.

## Required variables

- `DISPATCH_KEY`
- `DISPATCH_DIR`
- `DISPATCH_PORT`
- `GOVERNANCE_DIR`
- `GOVERNANCE_ROOT`
- `DRIFT_LATEST`
- `GITHUB_RAW_BASE`
- `QODER_PAT` only when the authenticated models endpoint is enabled

Optional bounded-write tuning:

- `MAX_HISTORY_BODY_BYTES` defaults to `65536`;
- `HISTORY_BODY_READ_TIMEOUT_SECONDS` defaults to `5`.

Values must be provisioned by the production secret mechanism and must never
be printed in preflight output.

## Verification before restart

1. Verify the source SHA-256 against the merged commit artifact.
2. Run `python3 -m py_compile` on the staged source.
3. Run `systemd-analyze verify` on the staged unit.
4. Verify the dedicated user can read the source, governance mirror, drift
   report, and environment file.
5. Verify the dedicated user can write only `/opt/pi/dispatch`.
6. Start a smoke instance on a temporary loopback port.
7. Confirm public governance endpoints and protected runtime endpoints.

## Rollback prerequisites

Before replacement, record and verify:

- current source SHA-256;
- current unit SHA-256;
- backup source path and hash;
- backup unit path and hash;
- current service state and start timestamp.

If the hardened service fails, restore both verified files, run
`systemctl daemon-reload`, restart once, and verify the previous endpoint
contract. Do not modify Caddy during this rollback.
