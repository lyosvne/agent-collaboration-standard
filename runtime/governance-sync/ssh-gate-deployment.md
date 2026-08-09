# Governance sync SSH gate deployment

Install the gate only after the helper deployment in `contract.md` is valid.
Run deployment commands as root.

## Accounts and filesystem

Use the dedicated account `aetheris-sync-deploy` only for this protocol.
It must have a locked password, no password or keyboard-interactive login, no
other keys, and no unrelated group memberships or services. It must not be a
member of `aetheris-governance-sync`. The protocol does not use a caller
delivery group or any supplementary group membership.

```sh
useradd --system --create-home \
  --home-dir /var/lib/aetheris-sync-deploy \
  --shell /bin/sh aetheris-sync-deploy
passwd --lock aetheris-sync-deploy
gpasswd -d aetheris-sync-deploy aetheris-governance-sync 2>/dev/null || true

install -o root -g root -m 0755 \
  runtime/governance-sync/aetheris-governance-sync-ssh \
  /usr/local/sbin/aetheris-governance-sync-ssh

install -d -o pi-governance-sync -g pi-governance-sync -m 0700 \
  /var/lib/aetheris-governance-sync/incoming

install -d -o root -g root -m 0755 \
  /var/lib/aetheris-sync-deploy
install -d -o aetheris-sync-deploy -g aetheris-sync-deploy -m 0700 \
  /var/lib/aetheris-sync-deploy/.ssh
install -o aetheris-sync-deploy -g aetheris-sync-deploy -m 0600 \
  /dev/null /var/lib/aetheris-sync-deploy/.ssh/authorized_keys
```

Install the canonical tmpfiles configuration into `/usr/lib/tmpfiles.d` for a
packaged deployment, or `/etc/tmpfiles.d` for a local administrator-managed
deployment. Install it in exactly one location; an `/etc` file with the same
name overrides the `/usr/lib` file. Then create the lock immediately and verify
the resulting inode. The same configuration recreates it during boot:

```sh
tmpfiles_dir=/usr/lib/tmpfiles.d
# For a local deployment instead, use: tmpfiles_dir=/etc/tmpfiles.d
install -d -o root -g root -m 0755 "$tmpfiles_dir"
install -o root -g root -m 0644 \
  runtime/governance-sync/tmpfiles/aetheris-governance-sync.conf \
  "$tmpfiles_dir/aetheris-governance-sync.conf"
systemd-tmpfiles --create "$tmpfiles_dir/aetheris-governance-sync.conf"
test -d /run/aetheris-governance-sync
test ! -L /run/aetheris-governance-sync
test "$(stat -c '%U:%G:%a' /run/aetheris-governance-sync)" = \
  "root:pi-governance-sync:750"
test -f /run/aetheris-governance-sync/gate.lock
test ! -L /run/aetheris-governance-sync/gate.lock
test "$(stat -c '%U:%G:%a' \
  /run/aetheris-governance-sync/gate.lock)" = \
  "root:pi-governance-sync:640"
```

Verify the deploy account is outside the retired caller group and all protocol
paths use the sync account's primary IDs:

```sh
passwd --status aetheris-sync-deploy
id aetheris-sync-deploy
sudo -u pi-governance-sync /usr/bin/python3 -I -c \
  'import os,pwd; u=pwd.getpwnam("pi-governance-sync"); assert (os.geteuid(),os.getegid()) == (u.pw_uid,u.pw_gid)'
test "$(stat -c '%U:%G:%a' /var/lib/aetheris-governance-sync/incoming)" = \
  "pi-governance-sync:pi-governance-sync:700"
test "$(stat -c '%U:%G:%a' /run/aetheris-governance-sync)" = \
  "root:pi-governance-sync:750"
test "$(stat -c '%U:%G:%a' /run/aetheris-governance-sync/gate.lock)" = \
  "root:pi-governance-sync:640"
! sudo -u pi-governance-sync test -w /run/aetheris-governance-sync
test "$(stat -c '%U:%G:%a' /var/lib/aetheris-sync-deploy)" = "root:root:755"
test "$(stat -c '%U:%G:%a' /var/lib/aetheris-sync-deploy/.ssh)" = \
  "aetheris-sync-deploy:aetheris-sync-deploy:700"
test "$(stat -c '%U:%G:%a' /var/lib/aetheris-sync-deploy/.ssh/authorized_keys)" = \
  "aetheris-sync-deploy:aetheris-sync-deploy:600"
! sudo -u aetheris-sync-deploy test -w /var/lib/aetheris-governance-sync/incoming
```

## SSH key restriction

Put the one synchronization public key in
`/var/lib/aetheris-sync-deploy/.ssh/authorized_keys` with this prefix on
the same physical line:

```text
restrict,command="sudo -n -u pi-governance-sync /usr/local/sbin/aetheris-governance-sync-ssh" ssh-ed25519 PUBLIC_KEY governance-sync
```

On OpenSSH versions without `restrict`, use the explicit equivalent:

```text
no-agent-forwarding,no-port-forwarding,no-X11-forwarding,no-pty,no-user-rc,command="sudo -n -u pi-governance-sync /usr/local/sbin/aetheris-governance-sync-ssh" ssh-ed25519 PUBLIC_KEY governance-sync
```

The file must contain exactly one nonblank, noncomment line and therefore
exactly one forced key:

```sh
test "$(grep -cEv '^[[:space:]]*(#|$)' \
  /var/lib/aetheris-sync-deploy/.ssh/authorized_keys)" -eq 1
```

Do not grant an unrestricted or second key to this account. The gate accepts
no local argv and only the five commands documented in
`ssh-gate-contract.md`.

## sshd restrictions

Apply a dedicated `Match User` block (or an equivalent independently tested
configuration) and validate it before reload:

```text
Match User aetheris-sync-deploy
    AuthenticationMethods publickey
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    PermitUserEnvironment no
    PermitUserRC no
    AllowAgentForwarding no
    AllowTcpForwarding no
    X11Forwarding no
    PermitTTY no
```

`PermitUserEnvironment no` is mandatory. Do not configure `AcceptEnv` for
`PATH`, `PYTHONPATH`, `PYTHONHOME`, `LD_*`, `BASH_ENV`, `ENV`, `GIT_*`, or
other execution-affecting variables; dangerous `AcceptEnv` entries must be
removed globally. If locale forwarding is operationally required, allow only
the explicit locale names `LANG` and `LC_*`; the gate still discards them and
uses its fixed helper environment.

```sh
sshd -t
sshd -T -C user=aetheris-sync-deploy,host=localhost,addr=127.0.0.1 |
  grep -E '^(authenticationmethods|passwordauthentication|kbdinteractiveauthentication|permituserenvironment|permituserrc|allowagentforwarding|allowtcpforwarding|x11forwarding|permittty) '
```

## Sudo and validation

Install and validate the repository sudoers drop-in:

```sh
install -o root -g root -m 0440 \
  runtime/governance-sync/sudoers/aetheris-governance-sync \
  /etc/sudoers.d/aetheris-governance-sync
visudo -cf /etc/sudoers.d/aetheris-governance-sync
sudo -l -U aetheris-sync-deploy
sudo -u aetheris-sync-deploy sudo -n -u pi-governance-sync \
  /usr/local/sbin/aetheris-governance-sync-ssh </dev/null
! sudo -u aetheris-sync-deploy sudo -n -u pi-governance-sync \
  /usr/local/sbin/aetheris-governance-sync --help
```

The drop-in sets `!use_pty` with a command-specific `Defaults!` entry for
`/usr/local/sbin/aetheris-governance-sync-ssh` only. Do not set `!use_pty`
globally or for the deploy account: all other sudo commands retain the host's
default PTY policy. The exception is required because `upload` carries an
opaque binary bundle from the SSH channel through sudo's stdin to the gate;
ordinary pipes must carry that stream without a sudo PTY relay.

The first sudo probe must reach the gate (and fail only because
`SSH_ORIGINAL_COMMAND` is absent). The helper probe must be denied. No
wildcard, alternate arguments, shell, or direct helper command is granted.

## Migration from the direct gate

Before enabling the new key, install the gate and sudoers drop-in, remove
`aetheris-sync-deploy` (and any legacy SSH deployment account) from the retired
caller group, and remove every old sudoers entry granting a group or deploy
account the helper. Only the repository rule granting `aetheris-sync-deploy`
the no-argument gate may remain. Replace the authorized-key forced command atomically with
the sudo form above, terminate old SSH sessions, then verify:

```sh
! id -nG aetheris-sync-deploy | tr ' ' '\n' | grep -Fx aetheris-governance-sync
! sudo -u aetheris-sync-deploy test -w /var/lib/aetheris-governance-sync/incoming
! sudo -u aetheris-sync-deploy sudo -n -u pi-governance-sync \
  /usr/local/sbin/aetheris-governance-sync --help
sudo -l -U aetheris-sync-deploy | grep -F \
  '/usr/local/sbin/aetheris-governance-sync-ssh ""'
```

Remove any legacy `.gate.lock` or abstract-socket assumptions. The gate now
uses the pre-created fixed root-owned lock inode inside its dedicated exact-mode
`0750` directory. Do not let `pi-governance-sync` create or replace files in
`/run/aetheris-governance-sync`. The standard `/run/lock` directory is not part
of the gate trust boundary; its conventional `1777` mode does not affect gate
validation.

Verify legacy upload, chunked upload, dry-run, apply, and cleanup from the
client without a remote shell:

```sh
git bundle create governance.bundle master
sha256=$(sha256sum governance.bundle | cut -d' ' -f1)
commit=$(git rev-parse master)
# stdin remains a binary byte stream through SSH and the sudo gate. The gate
# reads exactly the declared byte count and does not wait for channel EOF.
size=$(wc -c < governance.bundle | tr -d '[:space:]')
ssh GOVERNANCE_HOST "upload $size" < governance.bundle
# Resumable alternative: send canonical sequential chunks. Each successful
# non-final call returns chunk_uploaded with the next offset; retry a short
# block at the same offset. This example uses 1 MiB blocks.
chunk_size=$((1024 * 1024))
upload_id=$(openssl rand -hex 16)
offset=0
while test "$offset" -lt "$size"; do
  length=$chunk_size
  test $((offset + length)) -le "$size" || length=$((size - offset))
  response=$(
    dd if=governance.bundle bs=1 skip="$offset" count="$length" status=none |
      ssh GOVERNANCE_HOST "upload-chunk $upload_id $size $offset $length"
  ) || exit 1
  printf '%s\n' "$response" | python3 -c 'import json,sys; assert json.load(sys.stdin)["status"] in {"chunk_uploaded","uploaded"}'
  offset=$((offset + length))
done
ssh GOVERNANCE_HOST "dry-run $commit $sha256"
ssh GOVERNANCE_HOST "apply $commit $sha256"
ssh GOVERNANCE_HOST cleanup
```

Also verify rejection of a sixth command, malformed hashes, upload totals or
sizes of zero and more than 64 MiB, malformed 32-character lowercase
hexadecimal upload IDs, non-canonical decimal values, chunk ranges
where `offset >= total` or `offset + length > total`, and a login shell
request. Declare one byte more than the supplied stream for both upload forms
and verify `upload_short`; declare the exact stream size while keeping the
client side of the SSH channel open and verify the gate responds without
waiting for EOF. For chunked upload, verify it responds without waiting for EOF
and that a short later block rolls `.upload`
back to that block's starting offset while preserving all earlier complete
blocks; then retry that offset successfully. Verify an `offset 0` replay while
safe transaction state exists returns `upload_pending`, while overlapping,
skipped, out-of-order, and positive replayed offsets return
`upload_offset_mismatch` without mutation. Interleave a different ID and change
`total` at the correct offset; both must return
`upload_transaction_mismatch`. Verify every successful block
fsyncs `.upload`; the first block also fsyncs `.upload.meta` and the directory
before success. Only the final block may atomically publish
`governance.bundle`; it must remove `.upload.meta` and fsync the directory.
After each rejected first upload, the incoming directory must contain neither
`.upload` nor `.upload.meta`, and any previous `governance.bundle` must remain
unchanged. Create
symlink, FIFO, and directory fixtures at each fixed target name in a disposable
deployment and verify both upload and cleanup reject them without deleting the
inode. Hold an exclusive flock on
`/run/aetheris-governance-sync/gate.lock` from one invocation and verify each
of the five commands returns `already_running`. Also verify
`aetheris-sync-deploy` cannot create, replace, or unlink any fixed incoming
name.
