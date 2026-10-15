# 2. 있는지 확인하기

먼저 확인할 프롬프트를 하나 넣어 둡니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ echo '이 문서를 세 줄로 요약해 주세요.' > prompt.md
    $ promptq enqueue --name myapp/SUMMARIZE/1 --file prompt.md --on-dup ignore

`has`는 아무것도 출력하지 않고 종료 코드로만 답합니다. 자주 불러도 부담이 없습니다. `prefix:`는 글자 그대로 비교하므로 칸 경계인 `/`로 끝내세요. `list`는 상태와 이름을 보여 주고, 언제 그 상태가 되었는지 알고 싶으면 `--show-time`을 붙이세요.

    $ promptq has --matched prefix:myapp/
    $ promptq has --matched prefix:other/
    [1]
    $ promptq list
    pending myapp/SUMMARIZE/1

다음: [가져가서 처리하기](03_claim-and-dequeue.md)
