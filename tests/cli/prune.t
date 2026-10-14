`promptq prune-claimed` removes claimed prompts that have been held too long.
It requires an `older-than:` selector so it can never wipe everything by accident.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ promptq prune-claimed --matched prefix:GITHUB/
  promptq: error: prune-claimed requires an older-than: selector
  [2]
  $ promptq prune-claimed --matched older-than:0s
  promptq: error: duration must be greater than zero: '0s'
  [2]
  $ promptq prune-claimed --matched older-than:6
  promptq: error: duration must look like 30m, 6h, or 1d: '6'
  [2]

Pending prompts are never touched, and an empty result is not an error.

  $ echo p | promptq enqueue --name GITHUB/o/r/KIND/1 --file - --on-dup ignore
  $ promptq prune-claimed --matched older-than:6h
  $ promptq prune-claimed --matched older-than:6h --matched state:pending
  promptq: error: prune-claimed only targets claimed prompts
  [2]
  $ promptq list | wc -l | tr -d ' '
  1
