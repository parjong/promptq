# 5. 제목 붙이기

`--title`로 프롬프트에 한 줄 제목을 붙일 수 있습니다. 선택 사항이고, 이 프롬프트를 처리하는 세션의 이름처럼 사람이 보는 이름으로 쓰기 좋습니다. 제목은 `list`의 마지막 열과 `claim-one` 출력에 나옵니다. 앞뒤 공백 없는 한 줄이어야 하고 200자까지입니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ echo '이번 주 보고서를 작성해 주세요.' > prompt.md
    $ promptq enqueue --name myapp/REPORT/1 --title 'Write the weekly report' --file prompt.md --on-dup ignore
    $ promptq list
    pending myapp/REPORT/1 Write the weekly report
    $ promptq claim-one --matched prefix:myapp/REPORT/ | head -3
    status: claimed
    name: myapp/REPORT/1
    title: Write the weekly report
    $ promptq dequeue --name myapp/REPORT/1

이름에는 공백이 없으므로 스크립트에서는 `read -r state name title`로 읽으면 `title`이 줄의 나머지입니다.
