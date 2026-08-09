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

Every invocation resolves `pi-governance-sync` through `pwd.getpwnam` and
requires both its effective UID and effective GID. The incoming directory,
bundle, and `.upload` must use those same primary IDs. There is no caller-group
delivery semantics: `aetheris-sync-deploy` is not given incoming access, and no
supplementary group is consulted by the gate.

## Command protocol

Exactly these four canonical commands are accepted:

```text
upload
apply <40 lowercase hex commit> <64 lowercase hex sha256>
dry-run <40 lowercase hex commit> <64 lowercase hex sha256>
cleanup
```

There are no quoting, escaping, environment assignment, wildcard, option, or
shell semantics. Additional or repeated whitespace, additional arguments,
uppercase hex, and abbreviated object names are rejected.

## Gate lock

Every `upload`, `dry-run`, `apply`, and `cleanup` invocation opens the fixed
`/run/lock/aetheris-governance-sync-ssh-gate.lock` inode with `O_NOFOLLOW` and
takes a nonblocking `flock`. The inode must be a `root:pi-governance-sync`
`0640` regular file. `/run/lock` must resolve to a stable root-owned directory
that is neither world-writable nor writable by the sync group, so the
unprivileged `pi-governance-sync` gate cannot replace the lock. Contention
fails immediately with `already_running`.

The repository's canonical
`tmpfiles/aetheris-governance-sync.conf` declares that inode with systemd
tmpfiles type `f`, mode `0640`, owner `root`, and group
`pi-governance-sync`. Deployment installs that file under
`/usr/lib/tmpfiles.d` or `/etc/tmpfiles.d`, invokes `systemd-tmpfiles --create`,
and verifies the resulting metadata with `stat`. The tmpfiles boot service
therefore creates the lock after each boot before the gate is used.

This lock is independent from the helper's
`/run/lock/aetheris-governance-sync.lock`; the gate lock serializes protocol
operations, while the helper lock continues to protect mirror transactions.

While holding that lock, the gate opens the fixed incoming directory with
`O_DIRECTORY|O_NOFOLLOW` and validates that it is owned by the gate's
effective UID and GID and uses exact mode `0700`.

## Upload transaction

`upload` reads the bundle from standard input. The hard limit is 64 MiB
(67,108,864 bytes); the first byte beyond the limit fails the operation.

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
only the fixed `governance.bundle` and `.upload` names. Each existing target
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
