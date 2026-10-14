A prompt can carry a one-line title, for example to name the session that handles it.
The title is optional.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ P=GITHUB/octocat/hello
  $ echo 'Resolve the conflict in PR 12' | promptq enqueue --name $P/RESOLVE_PR_CONFLICT/12 --title 'Resolve conflict in PR 12' --file - --on-dup ignore
  $ echo 'Nothing special' | promptq enqueue --name $P/OTHER/3 --file - --on-dup ignore

`list` puts the title last, after the name. Names contain no spaces, so a script can read the
columns with `read -r state name title` and take the title as the rest of the line.

  $ promptq list
  pending GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12 Resolve conflict in PR 12
  pending GITHUB/octocat/hello/OTHER/3
  $ promptq list | while read -r state name title; do echo "[${title:-no title}]"; done
  [Resolve conflict in PR 12]
  [no title]

`claim-one` prints it right after the name, and only when there is one.

  $ promptq claim-one --matched prefix:$P/
  status: claimed
  name: GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12
  title: Resolve conflict in PR 12
  ---
  Resolve the conflict in PR 12
  $ promptq claim-one --matched prefix:$P/
  status: claimed
  name: GITHUB/octocat/hello/OTHER/3
  ---
  Nothing special

JSON always has the key, with null when there is no title.

  $ echo 'again' | promptq enqueue --name $P/OTHER/4 --file - --on-dup ignore
  $ promptq claim-one --matched prefix:$P/OTHER/4 --format json
  {"status": "claimed", "name": "GITHUB/octocat/hello/OTHER/4", "title": null, "enqueued_at": "*", "claimed_at": "*", "body": "again\n"} (glob)

A title must be a single line without leading or trailing spaces (exit 2, nothing is stored).

  $ echo p | promptq enqueue --name $P/BAD/1 --title ' padded' --file - --on-dup ignore
  promptq: error: title has leading or trailing whitespace
  [2]
  $ echo p | promptq enqueue --name $P/BAD/1 --title '' --file - --on-dup ignore
  promptq: error: title is empty
  [2]
  $ promptq has --matched prefix:$P/BAD/
  [1]
