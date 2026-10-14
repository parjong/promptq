`promptq home show` tells where the store is, without touching the disk.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ promptq home show | sed "s#$PWD#<tmp>#"
  <tmp>/queue
  $ promptq home show --explain | sed "s#$PWD#<tmp>#"
  path: <tmp>/queue
  source: PROMPTQ_HOME
  exists: no
  $ test -e queue || echo not created
  not created

The --home option beats the environment variable.

  $ promptq --home "$PWD/other" home show --explain | sed "s#$PWD#<tmp>#"
  path: <tmp>/other
  source: argument
  exists: no

Without any setting it falls back to the XDG state directory.

  $ unset PROMPTQ_HOME
  $ XDG_STATE_HOME="$PWD/state" promptq home show --explain | sed "s#$PWD#<tmp>#"
  path: <tmp>/state/promptq
  source: XDG_STATE_HOME
  exists: no

A relative path is refused, because it would depend on the current directory.

  $ PROMPTQ_HOME=relative promptq home show
  promptq: error: PROMPTQ_HOME must be an absolute path: 'relative'
  [2]
