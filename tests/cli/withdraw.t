`promptq withdraw` retracts a prompt that no Consumer has claimed yet.

  $ export PROMPTQ_HOME="$PWD/queue"
  $ P=GITHUB/o/r/KIND
  $ echo p | promptq enqueue --name $P/12 --file - --on-dup ignore
  $ echo p | promptq enqueue --name $P/120 --file - --on-dup ignore

Only the exact name is removed (12, not 120). A name that is not there exits 1.

  $ promptq withdraw --name $P/12
  $ promptq withdraw --name $P/12
  promptq: not found: GITHUB/o/r/KIND/12
  [1]
  $ promptq withdraw --name $P/999
  promptq: not found: GITHUB/o/r/KIND/999
  [1]
  $ promptq list
  pending GITHUB/o/r/KIND/120

A claimed prompt belongs to its Consumer: it is left alone and the exit code is 4.

  $ promptq claim-one --matched prefix:$P/ > /dev/null
  $ promptq withdraw --name $P/120
  promptq: claimed: GITHUB/o/r/KIND/120 (use --force to remove it)
  [4]
  $ promptq list
  claimed GITHUB/o/r/KIND/120

--force removes it whichever state it is in.

  $ promptq withdraw --name $P/120 --force
  $ promptq withdraw --name $P/120 --force
  promptq: not found: GITHUB/o/r/KIND/120
  [1]
  $ echo p | promptq enqueue --name $P/7 --file - --on-dup ignore
  $ promptq withdraw --name $P/7 --force
  $ promptq list
