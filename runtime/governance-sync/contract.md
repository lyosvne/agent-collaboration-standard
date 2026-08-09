# Governance sync helper contract

## Fixed resources

The installed helper is `/usr/local/sbin/aetheris-governance-sync`. These paths
are compiled into the program and cannot be overridden by arguments or the
environment:

| Resource | Path |
|---|---|
| Mirror | `/opt/pi/governance-mirror/repo` |
| Input bundle | `/var/lib/aetheris-governance-sync/incoming/governance.bundle` |
| Process lock | `/run/lock/aetheris-governance-sync.lock` |
| Receipts | `/var/lib/aetheris-governance-sync/receipts` |
| Backup refs | `refs/aetheris-governance-sync/backups/<operation-id>` |

## Identities, ownership, and modes

The SSH caller is the dedicated `aetheris-sync-deploy` identity. It is not a
member of `aetheris-governance-sync`, cannot write the incoming directory, and
may use sudo only to run the no-argument SSH gate as `pi-governance-sync`.
The gate, not the deploy account, deposits an atomically completed bundle at
the fixed incoming path. The deploy account has no sudo grant for the helper
and no write access to the mirror, incoming files, receipts, either lock,
helper, or sudoers rule. The dedicated `pi-governance-sync` account and its
primary group exclusively own the `0700` incoming directory and `0600`
bundle. It is the exclusive writer of incoming, the mirror, and runtime state.
It is not root and the helper rejects effective UID 0 even if it is invoked
outside sudoers.

The deployment contract is:

| Object | Owner:group | Mode / constraint |
|---|---|---|
| Installed helper | `root:root` | `0755`, not writable by the caller |
| Installed SSH gate | `root:root` | `0755`, not writable by the caller |
| Sudoers drop-in | `root:root` | `0440` |
| Mirror directory | `pi-governance-sync:pi-governance-sync` | owner UID and group ID must equal the helper effective IDs; no group/world write |
| Mirror `.git` directory | `pi-governance-sync:pi-governance-sync` | real in-mirror directory; owner UID and group ID must equal the helper effective IDs; no group/world write |
| Mirror `.git/config` | `pi-governance-sync:pi-governance-sync` | real regular file, group ID must equal the helper effective GID, no group/world write |
| Incoming directory | `pi-governance-sync:pi-governance-sync` | `0700`; only the trusted writer/root can modify fixed names; deploy cannot write |
| Incoming bundle and `.upload` | `pi-governance-sync:pi-governance-sync` | `0600`, regular non-symlink files; bundle published by atomic rename |
| Receipts directory | `pi-governance-sync:pi-governance-sync` | `0700` |
| Receipt files | `pi-governance-sync:pi-governance-sync` | `0600` |
| Helper lock | `pi-governance-sync:pi-governance-sync` | `/run/lock/aetheris-governance-sync.lock`, `0600`, regular non-symlink file |
| SSH gate lock directory | `root:pi-governance-sync` | `/run/aetheris-governance-sync`, exact mode `0750`, real non-symlink directory created at boot by the canonical `tmpfiles/aetheris-governance-sync.conf` |
| SSH gate lock | `root:pi-governance-sync` | `/run/aetheris-governance-sync/gate.lock`, `0640`, regular non-symlink file created after its dedicated directory by the canonical tmpfiles configuration |

The helper starts with umask `027`: repository files remain readable by the
`pi-governance-sync` group but are never group-writable. `pi-dispatch` uses
`pi-governance-sync` only as a supplementary read group; its primary group
remains `pi-dispatch`, and it receives no mirror ownership or write access.
Only `pi-governance-sync` owns and writes the mirror. The helper requires the
incoming directory to be a real directory owned by its effective UID and GID
and exactly mode `0700`. The bundle must be a real non-symlink regular file
owned by those same effective IDs and exactly mode `0600`; the opened file
descriptor must retain the validated inode, owner, group, and mode. It also
rejects a symlink, gitfile, escaped Git directory,
wrong owner/group, or group/world-writable mirror, `.git`, or `.git/config`. It
verifies inode identity again after Git inspection to fail closed on replacement
races.

### One-time migration of an existing mirror

Before enabling a reader on an existing mirror, run this migration once as
root. Exclude the writer for the complete migration: stop it and verify it is
not running, or retain the helper's exclusive lock while all commands and
postcondition checks run. The lock-based procedure is:

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

The result must leave all directories group-readable/traversable, all regular
files group-readable, and every path free of group/world write. The final
`find` is mandatory verification that every path has the required owner and
group and no `go+w` bit; do not restart a stopped writer unless it passes. In
particular, `pi-dispatch` must be able to read `.git/HEAD` and governance
documents through its supplementary group, but must not be able to create,
overwrite, or rename content in the work tree, `.git/refs`, or `.git/config`.

The sudoers command policy is exactly:

```sudoers
Defaults!/usr/local/sbin/aetheris-governance-sync-ssh secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin, env_keep += "SSH_ORIGINAL_COMMAND", !use_pty
aetheris-sync-deploy ALL=(pi-governance-sync) NOPASSWD: /usr/local/sbin/aetheris-governance-sync-ssh ""
```

The deploy account cannot sudo the helper. No `%aetheris-governance-sync`
sudo authorization exists. The gate requires the `pi-governance-sync`
effective UID and GID, then directly executes the helper without a nested
sudo. This no-argument gate is the deploy account's only sudo grant. The
`!use_pty` exception is scoped to that exact gate executable so its binary
stdin `upload` and
`upload-chunk <32hex_upload_id> <total> <offset> <length>` streams use
ordinary pipes; all other sudo commands retain the host's default PTY policy.
The compatible one-shot upload and resumable chunk protocol share the same
fixed gate lock, `.upload` staging inode, and `.upload.meta` transaction
record. Every complete chunk is fsynced; the first response additionally
requires metadata and directory fsync. A short chunk is truncated back to its
starting offset without discarding earlier complete chunks, and only the final
chunk atomically publishes `governance.bundle`, removes `.upload.meta`, and
fsyncs the directory. The full command and error contract is defined in
`ssh-gate-contract.md`.

## CLI

```text
aetheris-governance-sync \
  --bundle /var/lib/aetheris-governance-sync/incoming/governance.bundle \
  --commit <40 lowercase hexadecimal characters> \
  --sha256 <64 lowercase hexadecimal characters> \
  [--dry-run]
```

All three value options are mandatory. Abbreviated options, extra arguments,
alternate paths, uppercase hexadecimal, abbreviated commits, and malformed
SHA-256 values are rejected before any filesystem mutation.

`--dry-run` performs the same bundle, object, repository, and lock checks as an
apply operation. It does not update the mirror or create backups or receipts.
Its JSON output includes `would_change`.

## Fixed public-source helper

The separately installed
`/usr/local/sbin/aetheris-governance-sync-public` helper shares the mirror,
receipts, and immutable backup semantics of the existing bundle helper. It
downloads one immutable GitHub Release bundle and relays it to that unchanged
helper. Its compiled resources cannot be overridden by arguments or environment:

| Resource | Fixed value |
|---|---|
| Release API | `https://api.github.com/repos/lyosvne/agent-collaboration-standard` |
| Release tag | `governance-sync-<40 lowercase hex commit>` |
| Manifest asset | `governance-sync-manifest.json` |
| Bundle asset | `governance.bundle` |
| Fixed incoming bundle | `/var/lib/aetheris-governance-sync/incoming/governance.bundle` |
| Existing helper | `/usr/local/sbin/aetheris-governance-sync` |

Its complete CLI is exactly:

```text
aetheris-governance-sync-public --commit <40 lowercase hex> --dry-run
aetheris-governance-sync-public --commit <40 lowercase hex> --apply
```

Exactly one mode is mandatory. Abbreviations, extra arguments, uppercase or
short object names, URL, branch, path, and remote-name inputs are rejected.
The helper uses the fixed isolated interpreter `#!/usr/bin/python3 -I`.
Argument validation precedes the execution-identity check: malformed arguments
return `invalid_arguments`, while a syntactically valid request executed as
root returns `root_execution_forbidden`.
Like the bundle helper, it sets umask `027`, rejects effective UID 0, requires
safe incoming ownership/modes in this contract, and emits only stable JSON
errors without curl or helper stderr. Every invocation, including malformed
arguments and `--help`, emits exactly one JSON object on exactly one output
stream; CLI contract failures use `invalid_arguments`.

The only metadata URL is the literal release-by-tag endpoint under the fixed
API base. From its response the helper trusts only an exact `tag_name`, exact
`target_commitish`, and each asset's `name`, positive integer `id`, and positive
integer `size`. It ignores metadata-supplied API, browser, HTML, and redirect
URLs. It constructs every asset URL itself as
`https://api.github.com/repos/lyosvne/agent-collaboration-standard/releases/assets/<id>`.
The manifest and bundle names must each occur exactly once.

The helper invokes absolute `/usr/bin/curl` with `--disable`, an empty config,
a complete allowlist environment, empty proxy, closed stdin, `shell=False`,
HTTPS-only original and redirect protocols, TLS 1.2 minimum, redirect limit,
connect and total timeout, and maximum file size. Metadata, manifest, and
bundle are capped at 1 MiB, 16 KiB, and 64 MiB. It never inherits or sends a
GitHub token, proxy, netrc location, curl config, credential helper, or
execution-affecting environment variable.

JSON duplicate keys are rejected. The manifest exact schema is version 1,
exact requested commit, and a `bundle` object containing only
`name = governance.bundle`, positive bounded `size`, and 64-character lowercase
`sha256`. Extra or missing fields and bool-as-integer values fail closed.
Metadata bundle size, manifest size, actual regular-file size, and actual
SHA-256 must agree exactly.

After validation, the helper opens the effective-ID-owned exact-mode `0700`
incoming directory without following a symlink. If a valid fixed bundle
already exists, it returns `incoming_busy` immediately without changing that
inode. It creates fixed `.public-release` staging with
`O_EXCL|O_NOFOLLOW`, copies and fsyncs it as effective-ID-owned mode `0600`,
revalidates name-to-inode identity, atomically renames it to the fixed incoming
bundle, and fsyncs the directory. A `FileExistsError` while creating staging
also returns `incoming_busy`; the pre-existing staging name is never removed.
On a publish fault, cleanup considers only the inode created by that invocation
and unlinks it only while a fixed name still has the recorded identity.

It then invokes the unchanged bundle helper directly, with closed stdin,
`shell=False`, and only this fixed argv:

```text
/usr/local/sbin/aetheris-governance-sync \
  --bundle /var/lib/aetheris-governance-sync/incoming/governance.bundle \
  --commit <requested commit> \
  --sha256 <manifest sha256> \
  [--dry-run]
```

The existing helper independently validates the bundle, commit, fast-forward,
mirror state, backup, CAS, worktree, receipt, and rollback. The public helper
accepts only its exact dry-run, no-op, applied, or stable error JSON schema.
Raw output, multiple objects, extra fields, tracebacks, wrong commit/hash, and
malformed receipt or backup ref are never forwarded.

After helper execution, source cleanup checks that the fixed bundle still has
the device/inode recorded at publication. It returns `clean` only after unlink
and directory fsync, `pending` when unlink failed and the same owned inode is
still present, or `state-unknown` when identity or deletion durability cannot
be proved. It never unlinks a replacement inode. A zero-exit dry-run, no-op, or
applied result is preserved and receives exactly one `source_cleanup` field
with that enum, so a successful old-helper result is not overwritten by a
cleanup exception. A validated nonzero old-helper result is relayed unchanged
only when cleanup is `clean`; otherwise the helper returns the stable
`bundle_cleanup_pending` or `bundle_cleanup_state_unknown` error. Temporary
metadata, manifest, and downloaded bundle files are owner-only and
automatically removed.

## Apply transaction

The helper fails closed and performs these phases in order:

1. Acquire the fixed non-symlink, owner-only `0600` regular-file lock without
   waiting.
2. Validate the effective-ID-owned `0700` incoming directory and
   effective-ID-owned `0600` regular non-symlink bundle, then open the
   validated inode and copy it to an owner-only snapshot while hashing;
   reject inode metadata changes or a SHA-256 mismatch.
3. Verify only that pinned snapshot in an isolated bare repository, fetch the
   exact requested object, require it to be a commit, and run strict object
   validation.
4. Require the fixed mirror, its real in-mirror `.git` directory, and real
   `.git/config` to satisfy owner/mode constraints; require a completely clean
   work tree with `HEAD` attached to exactly `master`, then repeat inode checks.
5. Fetch without updating `FETCH_HEAD` and require the target to be a
   fast-forward of the old `master` using `merge-base --is-ancestor`.
6. If target equals `HEAD`, return `no-op` without creating a backup ref or
   receipt.
7. Create a backup ref in the fixed backup namespace pointing to the old
   `HEAD`.
8. Advance `refs/heads/master` with `update-ref` compare-and-swap, using the
   observed old commit as the expected value. `HEAD` remains attached.
9. Hard-reset the work tree to the new `master` and verify attached, clean
    postconditions.
10. Atomically publish a mode `0600` receipt and fsync its directory.

Any failure after `master` moves first restores `refs/heads/master` with a
second compare-and-swap from the failed target to the old commit, then
hard-resets and verifies the work tree. A receipt failure is a transaction
failure and also triggers this rollback. If either rollback step cannot be
verified, the helper fails closed with `rollback_failed`.

Receipt publication tracks whether the atomic rename has succeeded. If opening
or fsyncing the receipts directory fails after rename, the helper removes the
published success receipt and fsyncs the directory again before reporting
`receipt_write_failed`; only that proven cleanup permits mirror rollback. If
receipt removal or the cleanup directory fsync fails, publication state cannot
be proven. The helper reports the dedicated stable error
`receipt_state_uncertain` and does **not** roll back the mirror, preserving the
new commit so it remains consistent with a success receipt that may already be
durable. Operator inspection is required in that state.

### Backup ref retention

Backup refs are immutable, operation-ID-named recovery anchors. Once creation
succeeds, the helper never deletes or retargets one, including when master CAS,
work-tree update, receipt creation, or rollback later fails. A backup without
a matching successful receipt is therefore an intentional orphan that marks
an interrupted/failed operation, not garbage to remove automatically. An
operator may delete such refs only after incident review confirms the mirror
and work tree are healthy and the referenced commit is no longer needed;
retention/garbage collection is outside this helper.

## Receipt privacy

Receipts are allowlist-only JSON. They contain schema version, operation ID,
UTC timestamps, status, dry-run flag, requested/before/after commits, expected
bundle SHA-256, backup ref, and a stable error code. They never contain
command output, exception text, environment values, user-supplied paths, or
absolute backup paths.

## Results

Success prints one JSON object to stdout and exits `0`. Expected failures print
only a stable `error_code` JSON object to stderr and exit `1`. `argparse`
contract failures exit `2`. In particular, uncertain receipt publication emits
exactly the stable code `receipt_state_uncertain`, without exception or cleanup
details. The helper never prints Git stderr.

The public helper overrides `argparse` termination and formatting: every CLI
contract failure, including `--help`, prints exactly
`{"status":"error","error_code":"invalid_arguments"}` to stderr and exits `1`;
it emits no usage text and nothing on stdout.
