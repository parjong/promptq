# 3. 가져가서 처리하기

먼저 처리할 프롬프트를 하나 넣어 둡니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ echo '이 문서를 세 줄로 요약해 주세요.' > prompt.md
    $ promptq enqueue --name myapp/SUMMARIZE/1 --file prompt.md --on-dup ignore

`claim-one`은 가장 오래된 프롬프트를 하나 가져갑니다. 첫 줄은 항상 `status: claimed` 또는 `status: empty`이고, `---` 아래는 본문 그대로입니다. (가져간 시각은 `--show-time`을 붙이면 `claimed_at:` 줄로 나옵니다.)

    $ promptq claim-one --matched prefix:myapp/
    status: claimed
    name: myapp/SUMMARIZE/1
    ---
    이 문서를 세 줄로 요약해 주세요.

처리가 끝나면 `dequeue`로 지웁니다. 처리할 수 없으면 `release`로 큐에 돌려놓습니다.

    $ promptq dequeue --name myapp/SUMMARIZE/1

아직 아무도 가져가지 않은 프롬프트는 `withdraw`로 거둬들일 수 있습니다. 없으면 종료 코드 1을 돌려줍니다.

    $ promptq enqueue --name myapp/SUMMARIZE/2 --file prompt.md --on-dup ignore
    $ promptq withdraw --name myapp/SUMMARIZE/2
    $ promptq withdraw --name myapp/SUMMARIZE/2
    promptq: not found: myapp/SUMMARIZE/2
    [1]

이미 claim된 프롬프트는 Consumer의 것이므로 지우지 않고 종료 코드 4를 돌려줍니다. 꼭 지워야 하면 `--force`를 붙이세요. 이미 시작된 작업이 취소되지는 않습니다.

    $ promptq enqueue --name myapp/SUMMARIZE/3 --file prompt.md --on-dup ignore
    $ promptq claim-one --matched prefix:myapp/SUMMARIZE/3 > /dev/null
    $ promptq withdraw --name myapp/SUMMARIZE/3
    promptq: claimed: myapp/SUMMARIZE/3 (use --force to remove it)
    [4]
    $ promptq withdraw --name myapp/SUMMARIZE/3 --force

더 가져갈 것이 없으면 종료 코드 1을 돌려줍니다. 종료 코드 1을 실패로 받아들이는 호출자는 `--empty-ok`로 0을 받으세요.

    $ promptq claim-one --matched prefix:myapp/
    status: empty
    [1]
    $ promptq claim-one --matched prefix:myapp/ --empty-ok
    status: empty

다음: [오래된 claim 정리하기](04_prune-claimed.md)
