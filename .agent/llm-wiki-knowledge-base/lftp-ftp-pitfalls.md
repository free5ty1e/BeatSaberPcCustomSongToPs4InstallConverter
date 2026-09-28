---
name: lftp-ftp-pitfalls
description: "Every known lftp/GoldHEN-FTPD trap: cat output carries transfer banners, get -o refuses clobber, FSELF unpacked on download, & splits unquoted paths, exit 0 on failed puts. With the proven robust patterns for each."
metadata:
  type: root-cause
---

# lftp / GoldHEN FTPD Pitfalls (and the Robust Patterns)

The PS4's GoldHEN FTP server + lftp CLI have a recurring set of traps. Each
one has caused a real bug in this project — collected here so no future
session rediscovers them the hard way.

## 1. `cat` (and `get`-to-stdout) mixes banners into file content — CRITICAL

lftp prints progress/transfer banners like `156 bytes transferred` into the
SAME stdout stream as the file content. On slow transfers (the PS4's Wi-Fi),
the banner is emitted **every time**; on fast transfers it may never appear —
making this bug environment-dependent and invisible on a fast dev rig while
100% reproducible in the field.

**Bites:**
- Exp 221: `ps4_state.py` failed parsing PS4 `features.json` ("Extra data:
  line 7 column 1") — banner chatter around `cat` output → fixed with
  `json.JSONDecoder().raw_decode()` scanning from the first `{`.
- Exp 240: the release-validation script read `READ-FAILED` on EVERY PS4
  read (3 failing user runs across two "fixes") because `LFTP_CAT` extracted
  from the first `{` but left the TRAILING banner (`...}155bytestransferred`),
  and `json.loads` failed on every read. My "transient flake" diagnosis
  (Exp 239) was wrong — the bug was deterministic given a banner-emitting link.

**Robust patterns (in order of preference):**
1. **Download to a temp FILE via `get`** — the banner goes to stderr/progress,
   never into the file. This is the transport the pipeline's own
   redirect-sync has used across hundreds of deploys.
   ```bash
   tmpd=$(mktemp -d)   # NOT mktemp — see pitfall 2
   lftp -u anonymous -e "get <remote> -o $tmpd/f; quit" "$IP:2121"
   ```
2. **If parsing a stream, extract from the first `{` to the LAST `}`** —
   immune to both leading and trailing chatter — or use
   `json.JSONDecoder().raw_decode()` on the first JSON object.

## 2. `get -o <file>` REFUSES to clobber an existing file

`get: <path>: File exists` — lftp will not overwrite. `mktemp` pre-creates a
file, so `get -o $(mktemp)` always fails with a 0-byte result (Exp 240: caught
by testing before hand-off after the first transport fix silently broke
every read this way). **Use `mktemp -d` and write to `$tmpd/f`.**

## 3. `put` exits 0 even when the transfer failed

lftp's command language can report success while the upload silently failed
(Exp 224: the `&`-path bug made the Scream&Shout upload vanish with exit 0).
**Never trust lftp's exit code for uploads** — verify by listing the remote
file and comparing sizes (`deploy_to_ps4` in the pipeline does this).

## 4. Unquoted paths split at `&` and other shell metacharacters

`Scream&Shout` → lftp ran `Scream` and then a shell command `Shout`
("Shout: command not found"). **Every path in every lftp invocation must be
quoted** — the pipeline's `_ftp_quote()` wraps all 21 call sites.

## 5. Downloading the .prx unpacks FSELF → byte-compare is invalid

GoldHEN FTPD unpacks FSELF on download: the local file is FSELF
(magic `4f153d1d`) but a downloaded copy is bare ELF (`7f454c46`) and a
different size. **Verify .prx uploads by strings, never md5** (Exp 221) —
`b'v0.8047' in downloaded_bytes` is the reliable check.

## 6. Anonymous login needs an explicit password form in some contexts

`lftp -u anonymous` can prompt/fail (`GetPass() failed`) in non-interactive
contexts. The reliable form used throughout this project:
`lftp -u anonymous:anonymous ... $IP:2121` (user AND password, port as part
of the host or `-p`).

## 7. Banner-contaminated interactive output

`lftp -e "cat ..."` in a terminal also shows the login banner
(`open: GetPass() failed -- assume anonymous login` on stderr). Filter
stderr, but never let stdout-parsing assume clean content (see pitfall 1).

See also: [[ps4-file-system-redirects]] (topology + command reference),
[[feature-flags]] (ps4_state.py reads), [[pack-scope-auto-discovery]]
(the deployed-state vs local-cache rule that several of these bugs violated).
