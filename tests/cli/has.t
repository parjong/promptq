`promptq has` is a cheap hint for hooks: it prints nothing and answers with its exit code.

  $ export PROMPTQ_HOME="$PWD/queue"

A store that does not exist yet is an empty queue, and asking does not create it.

  $ promptq has --matched prefix:GITHUB/octocat/hello/
  [1]
  $ test -e queue || echo not created
  not created

  $ echo p | promptq enqueue --name GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/1 --file - --on-dup ignore
  $ promptq has --matched prefix:GITHUB/octocat/hello/

A prefix is a literal string, so `hello` does not match `hello.world`.

  $ promptq has --matched prefix:GITHUB/octocat/hello.world/
  [1]
  $ echo p | promptq enqueue --name GITHUB/octocat/hello.world/RESOLVE_PR_CONFLICT/1 --file - --on-dup ignore
  $ promptq has --matched prefix:GITHUB/octocat/hello.world/

`has` only accepts selectors that can be answered from names, to keep it fast.

  $ promptq has --matched older-than:1h
  promptq: error: has does not accept older-than: selectors
  [2]
  $ promptq has --matched regex:.*
  promptq: error: regex: selectors are not supported yet
  [2]

With --quiet a broken store counts as "nothing", so a hook never gets in the way.

  $ rm queue/manifest.json
  $ promptq has --matched prefix:GITHUB/
  promptq: error: * (glob)
  [3]
  $ promptq has --quiet --matched prefix:GITHUB/
  [1]
