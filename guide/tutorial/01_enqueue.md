# 1. 프롬프트 넣기

저장소 위치는 `PROMPTQ_HOME`으로 정합니다. `promptq home show`로 어디인지 확인할 수 있습니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ promptq home show --explain | sed "s#$PWD#.#"
    path: ./queue
    source: PROMPTQ_HOME
    exists: no

이름은 `/`로 구분한 계층입니다. 각 칸에는 영문자, 숫자, `.`, `_`, `-`만 쓸 수 있고, promptq는 이름을 바꾸지 않고 검증만 합니다. 같은 이름이 이미 있을 때의 동작은 `--on-dup`으로 항상 직접 적습니다 (지금은 `ignore`만 있습니다).

    $ echo '이 문서를 세 줄로 요약해 주세요.' > prompt.md
    $ promptq enqueue --name myapp/SUMMARIZE/1 --file prompt.md --on-dup ignore

같은 이름을 다시 넣으면 무시되고 종료 코드 1로 알려 줍니다.

    $ promptq enqueue --name myapp/SUMMARIZE/1 --file prompt.md --on-dup ignore
    promptq: ignored: myapp/SUMMARIZE/1 already exists (pending)
    [1]

스케줄 잡처럼 같은 일을 반복해서 넣는 Producer에서는 "이미 있음"이 정상입니다. `--dup-ok`를 주면 종료 코드 0으로 끝납니다. 안내 메시지는 그대로 나오고, 잘못된 입력(2)이나 저장소 오류(3)는 그대로 실패합니다.

    $ promptq enqueue --name myapp/SUMMARIZE/1 --file prompt.md --on-dup ignore --dup-ok
    promptq: ignored: myapp/SUMMARIZE/1 already exists (pending)

다음: [있는지 확인하기](02_has-and-list.md)
