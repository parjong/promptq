Usage errors exit with status 2.

  $ promptq 2>/dev/null
  [2]
  $ promptq home 2>/dev/null
  [2]
  $ promptq no-such-command 2>/dev/null
  [2]

The version is printed from the package metadata.

  $ promptq --version
  promptq \d+\.\d+.* (re)
