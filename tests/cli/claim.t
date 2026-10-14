A consumer takes one prompt at a time with `claim-one`, handles it, then calls `dequeue`.
Several prompts are handled by repeating until the queue reports `status: empty`.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ P=GITHUB/octocat/hello
  $ printf 'first\n  indented\n' | promptq enqueue --name $P/KIND/1 --file - --on-dup ignore
  $ printf 'second' | promptq enqueue --name $P/KIND/2 --file - --on-dup ignore

The oldest prompt comes first. After the `---` line the body is printed byte for byte.

  $ promptq claim-one --matched prefix:$P/
  status: claimed
  name: GITHUB/octocat/hello/KIND/1
  ---
  first
    indented
  $ promptq list
  claimed GITHUB/octocat/hello/KIND/1
  pending GITHUB/octocat/hello/KIND/2

The time of the claim is printed only on request, with --show-time.

  $ promptq release --name $P/KIND/1
  $ promptq claim-one --matched prefix:$P/ --show-time | head -3
  status: claimed
  name: GITHUB/octocat/hello/KIND/1
  claimed_at: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ (re)

Scripts can ask for JSON, where the body is escaped safely and timestamps are always present.

  $ promptq claim-one --matched prefix:$P/ --format json
  {"status": "claimed", "name": "GITHUB/octocat/hello/KIND/2", "enqueued_at": "*", "claimed_at": "*", "body": "second"} (glob)

Nothing left: exit 1 by default, or exit 0 with --empty-ok for callers that treat 1 as a failure.

  $ promptq claim-one --matched prefix:$P/
  status: empty
  [1]
  $ promptq claim-one --matched prefix:$P/ --empty-ok --format json
  {"status": "empty"}

`has` and `claim-one` only take selectors that can be answered from names.

  $ promptq claim-one --matched older-than:1h
  promptq: error: claim-one does not accept older-than: selectors
  [2]

When the work is done the prompt is removed. Doing it twice is harmless but reported.

  $ promptq dequeue --name $P/KIND/1
  $ promptq dequeue --name $P/KIND/1
  promptq: not claimed: GITHUB/octocat/hello/KIND/1
  [1]

A prompt that cannot be handled goes back to the queue instead.

  $ promptq release --name $P/KIND/2
  $ promptq release --name $P/KIND/2
  promptq: not claimed: GITHUB/octocat/hello/KIND/2
  [1]
  $ promptq has --matched prefix:$P/

A freshly claimed prompt is never considered stale, however long it waited in the queue.

  $ promptq claim-one --matched prefix:$P/ > /dev/null
  $ promptq prune-claimed --matched older-than:1h
  $ promptq prune-claimed --matched older-than:1h --dry-run
  $ promptq list
  claimed GITHUB/octocat/hello/KIND/2
