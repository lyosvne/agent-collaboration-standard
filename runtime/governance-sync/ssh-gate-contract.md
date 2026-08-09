# Governance sync SSH gate contract

## Entry point and identity

`/usr/local/sbin/aetheris-governance-sync-ssh` has the fixed isolated
interpreter line `#!/usr/bin/python3 -I`. The one `authorized_keys` entry for
the password-locked `aetheris-sync-deploy` account uses this forced command:

```text
sudo -n -u pi-governance-sync /usr/local/sbin/aetheris-governance-sync-ssh
```

The gate accepts no process arguments and reads only the sudoers-preserved
`SSH_ORIGINAL_COMMAND`. Sudoers permits `aetheris-sync-deploy` to run exactly
that no-argument gate as `pi-governance-sync`; it does not permit the deploy
account to run the helper.

The `upload` and `upload-chunk` payloads are binary streams from the SSH channel through sudo to
the gate's standard input. The command-specific
`Defaults!/usr/local/sbin/aetheris-governance-sync-ssh !use_pty` setting keeps
that stream on ordinary pipes instead of sudo's PTY relay. This exception
applies only to the gate executable; `use_pty` and every other sudo default
remain unchanged for all other commands.

Every invocation resolves `pi-governance-sync` through `pwd.getpwnam` and
requires both its effective UID and effective GID. The incoming directory,
bundle, `.upload`, and `.upload.meta` must use those same primary IDs. There is no caller-group
delivery semantics: `aetheris-sync-deploy` is not given incoming access, and no
supplementary group is consulted by the gate.

## Command protocol

Exactly the five legacy bundle command forms and these two public-source forms
are accepted:

```text
upload <decimal_size>
upload-chunk <32 lowercase hex upload_id> <total> <offset> <length>
apply <40 lowercase hex commit> <64 lowercase hex sha256>
dry-run <40 lowercase hex commit> <64 lowercase hex sha256>
cleanup
sync-public <40 lowercase hex commit> dry-run
sync-public <40 lowercase hex commit> apply
```

`decimal_size` is the canonical base-10 byte length: ASCII digits without a
sign or leading zero, in the inclusive range 1 through 67,108,864 (64 MiB).
The `upload_id` is exactly 32 lowercase hexadecimal characters. The chunk
`total` and `length` use the same nonzero canonical decimal form;
`total` is at most 64 MiB. `offset` is canonical decimal zero or a positive
integer without a leading zero. A chunk is accepted syntactically only when
`offset < total` and `length <= total - offset`.
There are no quoting, escaping, environment assignment, wildcard, option, or
shell semantics. Additional or repeated whitespace, additional arguments,
uppercase hex, abbreviated object names, and non-canonical or out-of-range
upload sizes are rejected.
The public-source forms accept no URL, branch, path, remote name, SHA-256,
environment assignment, or fourth argument.

## Gate lock

Every `upload`, `upload-chunk`, `dry-run`, `apply`, `cleanup`, and
`sync-public` invocation
opens the same fixed
`/run/aetheris-governance-sync/gate.lock` inode with `O_NOFOLLOW` and
takes a nonblocking `flock`. The inode must be a `root:pi-governance-sync`
`0640` regular file. Its dedicated `/run/aetheris-governance-sync` parent must
be a real, non-symlink `root:pi-governance-sync` directory with exact mode
`0750`, and resolving it must preserve the same device and inode. These exact
requirements prevent the unprivileged `pi-governance-sync` gate from replacing
the lock. The ownership or mode of the separate standard `/run/lock` directory,
including the normal `1777` mode on some systems, is irrelevant. Contention
fails immediately with `already_running`.

The repository's canonical `tmpfiles/aetheris-governance-sync.conf` first
declares the dedicated directory with systemd tmpfiles type `d`, mode `0750`,
owner `root`, and group `pi-governance-sync`, then declares the lock inode with
type `f`, mode `0640`, and the same owner and group. Deployment installs it under
`/usr/lib/tmpfiles.d` or `/etc/tmpfiles.d`, invokes `systemd-tmpfiles --create`,
and verifies both objects' type, non-symlink status, ownership, and exact mode.
The tmpfiles boot service therefore creates the directory before the lock after
each boot and before the gate is used.

This lock is independent from the helper's
`/run/lock/aetheris-governance-sync.lock`; the gate lock serializes protocol
operations, while the helper lock continues to protect mirror transactions.

For the five legacy commands, while holding that lock, the gate opens the fixed
incoming directory with
`O_DIRECTORY|O_NOFOLLOW` and validates that it is owned by the gate's
effective UID and GID and uses exact mode `0700`.
The two `sync-public` forms hold the same root-owned gate lock but never open,
validate, read, or modify incoming.

## Upload transaction

`upload <decimal_size>` reads the bundle as opaque binary bytes from standard
input without text decoding, newline conversion, or buffering the complete
payload in memory. The declared size has a hard inclusive range of 1 byte
through 64 MiB (67,108,864 bytes). The gate repeatedly reads at most the
remaining declared byte count, so partial pipe reads are accumulated. EOF
before all declared bytes arrive fails with `upload_short`; no partial upload
is published. As soon as exactly the declared byte count has been read, the
gate completes the transaction without making another read and without
waiting for EOF. This permits the client to keep the SSH channel open while it
waits for the gate's response.

The only destination is
`/var/lib/aetheris-governance-sync/incoming/governance.bundle`. The gate opens
the fixed incoming directory with `O_NOFOLLOW`, requires a real directory with
effective UID/GID and exact mode `0700`, then creates only the fixed
same-directory `.upload` file with `O_CREAT|O_EXCL|O_NOFOLLOW`.

Before accepting content, the gate calls `fchown(fd, sync_uid, sync_gid)` and
`fchmod(fd, 0600)`. It verifies through `fstat` that the open inode remains a
regular file with those IDs and mode, fsyncs it, closes it, and atomically
renames it over the fixed bundle name. The existing bundle, if any, must
already be an effective-ID-owned `0600` regular file; symlinks, FIFOs, and directories
are rejected. After rename, the incoming directory is fsynced. No partial
upload is published.

`upload-chunk <upload_id> <total> <offset> <length>` is the resumable
counterpart to `upload`. It uses the same incoming directory, the fixed
`.upload` staging name, fixed `.upload.meta` transaction name, effective-ID
ownership and mode checks, fixed shared gate lock, binary length-bounded reads,
and 64 MiB total limit. `offset 0` exclusively creates both files as
effective-ID-owned `0600` regular files. `.upload.meta` contains canonical JSON
recording the exact `upload_id` and `total`. The first chunk is acknowledged
only after `.upload` and `.upload.meta` are fsynced and the incoming directory
is fsynced, making the two fixed transaction names durable. Existing safe state
fails with `upload_pending`.

A positive offset opens `.upload` with `O_APPEND` and requires both fixed files
to exist. Their open inodes must still be the fixed-name inodes with exact
ownership and mode; `.upload` must have exact size `offset`; and the metadata
must exactly match the command's `upload_id` and `total`. A different ID or
total fails with `upload_transaction_mismatch`. Missing state or any
nonsequential, overlapping, gapped, or replayed offset fails with
`upload_offset_mismatch`. Rejected interleaved and replayed requests do not
mutate either transaction file.

Each invocation reads exactly `length` bytes without waiting for EOF and
appends them at `offset`. A complete non-final chunk is fsynced before success
and remains as `.upload`; the response is
`{"status":"chunk_uploaded","offset":<next_offset>,"total":<total>}`. If EOF
or a read/write failure occurs after part of the current chunk, the gate
truncates the same open inode back to `offset` and fsyncs it. Thus a short read
returns `upload_short`, rolls back only that block, and preserves every
previously completed block. A failed first block identity-checks and unlinks
each new fixed transaction inode, then makes both removals durable with a
directory fsync. Any required truncate, unlink, file fsync, or directory fsync
failure returns `upload_state_unknown`.

Only a chunk satisfying `offset + length == total` is final. After fsyncing
that block, the gate revalidates the exact staging size, inode, destination,
ownership, and mode, closes the descriptors, atomically renames `.upload` to
`governance.bundle`, unlinks `.upload.meta`, and fsyncs the incoming directory.
Only then does it return the legacy-compatible `{"status":"uploaded"}`
response. No intermediate block is published. A post-rename metadata unlink
or directory fsync failure returns `upload_state_unknown`.

If the rename succeeds but the following directory fsync fails, the gate
returns only the stable `upload_state_unknown` error. The bundle may already be published,
so the gate does not claim failure or attempt to remove the renamed
destination; operator/client reconciliation is required.

Only the trusted `pi-governance-sync` writer and root can modify incoming
names; `aetheris-sync-deploy` cannot. Even within that trust boundary, any
pre-rename error closes the descriptor and removes `.upload` only if the
fixed name still resolves to the exact regular-file inode created by that
invocation, then fsyncs the directory. An existing completed bundle is left
untouched.

## Cleanup transaction

`cleanup` accepts no arguments. Under the gate lock it considers
only the fixed `governance.bundle`, `.upload`, and `.upload.meta` names. Each existing target
must be an effective-ID-owned `0600` regular file. If either name is a symlink, FIFO,
directory, or otherwise unsafe inode, cleanup fails before deleting anything.
The fixed-name metadata is collected before any deletion, which is sufficient
because only the trusted writer executing the serialized gate (or root) can
replace those inodes. It never scans the directory and never removes any
other name. After deleting the validated fixed files, it fsyncs the incoming
directory and returns one JSON object listing the removed fixed names.
If any unlink succeeds, cleanup fsyncs the directory in its `finally` path.
When that fsync succeeds but a later unlink has failed, cleanup returns only
the stable `cleanup_partial` error. If the directory fsync fails after any
deletion, cleanup instead returns `cleanup_state_unknown`, regardless of
whether an unlink also failed, because the durability of every completed
deletion is unknown. Neither partial nor unknown state ever masquerades as a
complete cleanup.

## Helper execution

The gate already runs with the `pi-governance-sync` effective UID and GID.
`apply` and `dry-run` therefore invoke the installed helper directly, without
sudo, using an argv array with `shell=False`, a fixed environment, closed
stdin, and these fixed prefix arguments:

```text
/usr/local/sbin/aetheris-governance-sync \
  --bundle /var/lib/aetheris-governance-sync/incoming/governance.bundle \
  --commit <commit> --sha256 <sha256>
```

`dry-run` appends the literal `--dry-run`. The SSH command text is never
forwarded to a shell or interpolated into an executable string.

The gate captures both helper stdout and stderr. It accepts and re-serializes
only one JSON object with an allowlisted schema: the expected
`dry-run`/`applied`/`no-op` success shape on zero exit, or exactly
`{"status":"error","error_code":"..."}` on nonzero exit. Unexpected fields,
multiple JSON values, non-JSON output, mixed stdout/stderr, oversized output,
or values that do not match the requested commit and SHA fail with a stable
gate error. Raw helper stderr, sudo diagnostics, exception text, and
tracebacks are never forwarded. The gate preserves a validated helper exit
status and converts all other failures to a stable JSON `error_code`.

For `sync-public`, the gate instead uses exactly this direct argv:

```text
/usr/local/sbin/aetheris-governance-sync-public \
  --commit <commit> --dry-run
/usr/local/sbin/aetheris-governance-sync-public \
  --commit <commit> --apply
```

It again closes stdin, uses `shell=False`, and supplies no SSH command text or
ambient URL, branch, path, or credential value. The public helper's error JSON
must contain exactly `status=error` and a stable `error_code`. Successful
dry-run JSON must contain exactly `status`, `before_commit`, `commit`,
`remote_master`, and boolean `would_change`, with `would_change` agreeing with
the two commits. No-op additionally requires equal requested/before commits
and a null backup. Applied JSON requires the requested commit, a full remote
master, a receipt basename, and a backup in the fixed namespace. Unexpected
fields, malformed values, mixed output streams, multiple JSON values, raw
stderr, URLs, or tracebacks are replaced by a stable gate error.
