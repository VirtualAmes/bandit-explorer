# Permission-friendly command style — MANDATORY

Brian approves permission prompts by hand; every novel command *shape* costs him
a sign-off, and a prompt that fires constantly stops carrying information —
which is how a genuinely destructive command gets waved through alongside
ninety harmless ones. Portable from Strato-Xen's `docs/COMMAND-STYLE.md` and
`docs/ANALYZABLE-COMMANDS.md`.

1. **One command per call.** Not `a && b && c`. Each of `git add`, `git commit`,
   `git push` is individually recognisable; the chain is not.
2. **Never pipe a program into an interpreter.** No `python3 - <<PY`, no
   `node -e "..."`, no `bash -c "..."`. Write the script to a file with the
   Write tool, then run the named file.
3. **Prefer the dedicated tools** (Read/Grep/Edit/Write) over `cat`/`sed`/
   `awk`/`echo >` — they are structured operations, and they don't prompt.
4. **Use `-C` instead of `cd`.** `git -C /path status` is analyzable;
   `cd /path && git status` changes what every later path means. Never head a
   compound with `cd` — the shell cwd silently resets between calls.
5. **Long text goes in a file, not an argument.** `git commit -F file`,
   `gh pr create --body-file file`. A quoted 2,000-character string with
   backticks is unparseable, and a stray backtick becomes shell execution.
6. **No inline env-var prefixes** beyond the allowlisted ones in
   `.claude/settings.json`. Pass a CLI flag or add a script target.
7. **No decorative shell.** Every `echo "exit=$?"` or pipe-to-awk flourish is
   its own prompt. Print from the program.
8. **Deliberately still prompting — do not route around:** `rm`, `mv` outside
   temp, `launchctl`, `security` (Keychain), `curl` to anything non-localhost,
   `ssh` to new hosts, `ALLOW_PROD_MERGE=1`. Those prompts are the point.
9. **GitHub calls are REST** (`gh api repos/...`) in any committed script; the
   `gh pr list`/`gh issue list` shortcuts ride GraphQL, which has failed
   independently of REST. Interactive throwaway use is fine.

## Checkout ownership

The primary checkout belongs to Brian (and the coordinator session in his
pane). Every worker session, before any git operation, creates or reuses its
own worktree under `.claude/worktrees/<topic>` and works there. Two sessions
sharing one working directory race on HEAD itself.
