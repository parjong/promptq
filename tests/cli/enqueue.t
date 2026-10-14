A producer adds prompts with `promptq enqueue`; `--on-dup` is required so the behavior
for an existing name is always visible where the command is written.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ printf 'Resolve the merge conflict in PR 12\n' > prompt.md
  $ promptq enqueue --name GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 --file prompt.md --on-dup ignore
  $ promptq has --matched prefix:GITHUB/octocat/hello/
  $ promptq list
  pending GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12

Enqueueing the same name again is ignored (exit 1) and tells which state it is in.

  $ promptq enqueue --name GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 --file prompt.md --on-dup ignore
  promptq: ignored: GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 already exists (pending)
  [1]

A producer that runs again and again, such as a scheduled job, can treat "already there" as
success with --dup-ok. The note is still printed, and real errors keep their exit codes.

  $ promptq enqueue --name GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 --file prompt.md --on-dup ignore --dup-ok
  promptq: ignored: GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 already exists (pending)
  $ promptq enqueue --name bad/ --file prompt.md --on-dup ignore --dup-ok 2>/dev/null
  [2]

`list` shows when each prompt entered its state only on request.

  $ promptq list --show-time --matched prefix:GITHUB/octocat/hello/RESOLVE
  pending \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 (re)

The prompt can come from stdin.

  $ echo 'Check the outdated issue' | promptq enqueue --name GITHUB/octocat/hello/CHECK_OUTDATED_ISSUE/3 --file - --on-dup ignore
  $ promptq list --matched prefix:GITHUB/octocat/hello/CHECK
  pending GITHUB/octocat/hello/CHECK_OUTDATED_ISSUE/3

Bad input is a usage error (exit 2), and nothing is stored.

  $ promptq enqueue --name bad/ --file prompt.md --on-dup ignore
  promptq: error: .* (re)
  [2]
  $ promptq enqueue --name x/1 --file missing.md --on-dup ignore
  promptq: error: cannot read 'missing.md': [Errno 2] No such file or directory: 'missing.md'
  [2]
  $ promptq enqueue --name x/1 --file prompt.md 2>/dev/null
  [2]
  $ promptq list | wc -l | tr -d ' '
  2

The store records who created it.

  $ promptq store check | sed "s#$PWD#<tmp>#"
  path: <tmp>/queue
  exists: yes
  store: dir
  store_version: 1
  min_reader: 0.0.1
  name_rules: 1
