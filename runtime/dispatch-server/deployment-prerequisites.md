# Dispatch Server Deployment Prerequisites

This document defines preflight requirements only. It does not authorize or
perform deployment.

## Identity and files

- Create the system identity `pi-dispatch:pi-dispatch` with no login shell.
- Add `pi-dispatch` to `pi-governance-sync` only as a supplementary read group;
  keep its primary group as `pi-dispatch` and grant it no mirror ownership or
  write permission.
- Install the canonical Python source as `root:root`, mode `0644`.
- Keep source directories traversable but not writable by `pi-dispatch`.
- Create `/opt/pi/dispatch` as `pi-dispatch:pi-dispatch`, mode `0750`.
- Keep the governance mirror and drift report readable by `pi-dispatch`.
- Create `/opt/pi-orchestrator/config/dispatch.env` as
  `root:pi-dispatch`, mode `0640`.

The dedicated environment file may contain only variables required by this
service. It must not reuse the shared orchestrator environment.

Before the first restart with the supplementary group, migrate the existing
mirror once as root. The migration must exclude the writer for its entire
duration: either stop the governance-sync writer and verify it is no longer
running, or retain an exclusive lock on
`/run/lock/aetheris-governance-sync.lock` while every command below runs.
The lock-based procedure is:

```sh
lock=/run/lock/aetheris-governance-sync.lock
mirror=/opt/pi/governance-mirror/repo
(
  flock -x 9
  chown pi-governance-sync "$lock"
  chgrp pi-governance-sync "$lock"
  chmod 0600 "$lock"
  chown -R pi-governance-sync "$mirror"
  chgrp -R pi-governance-sync "$mirror"
  find "$mirror" \( -type d -o -type f \) -exec chmod g+rX {} +
  chmod -R go-w "$mirror"
  bad=$(find "$mirror" \
    \( ! -user pi-governance-sync -o ! -group pi-governance-sync -o -perm /022 \) \
    -print -quit)
  test -z "$bad"
) 9>>"$lock"
```

This migration makes directories group-readable/traversable and files
group-readable (while preserving executable files), recursively removes group
and world write from every existing mirror path, and leaves
`pi-governance-sync` as the only mirror owner/writer. The final `find` is a
mandatory postcondition check for the owner, group, and absence of any `go+w`
bit. Do not restart a stopped writer until it passes. The canonical systemd unit
supplies `SupplementaryGroups=pi-governance-sync`; do not grant `pi-dispatch`
write access through ACLs or another group.

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
4. Verify the dedicated user, through its supplementary
   `pi-governance-sync` group, can read mirror `HEAD` and governance documents.
5. Verify the dedicated user cannot write the mirror work tree, `.git/refs`,
   or `.git/config`, and can write only `/opt/pi/dispatch`.
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
