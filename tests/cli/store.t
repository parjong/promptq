`promptq store check` verifies a store without creating or changing it.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ promptq store check | sed "s#$PWD#<tmp>#"
  path: <tmp>/queue
  exists: no
  $ test -e queue || echo not created
  not created

A directory with unrelated content is not guessed at; it is a store error (exit 3).

  $ mkdir queue
  $ echo hello > queue/other.txt
  $ promptq store check 2>err; echo "exit=$?"
  exit=3
  $ sed "s#$PWD#<tmp>#" err
  promptq: error: <tmp>/queue.*manifest.* (re)
