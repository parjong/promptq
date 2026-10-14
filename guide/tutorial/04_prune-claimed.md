# 4. 오래된 claim 정리하기

Consumer가 죽으면 claim된 항목이 남습니다. Producer가 새로 넣기 전에 정리하세요. `older-than:`은 단위(`s`, `m`, `h`, `d`)가 필수이고, 처리 시간보다 충분히 길게 잡습니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ promptq prune-claimed --matched older-than:6h --matched prefix:myapp/

`--dry-run`을 붙이면 지우지 않고 대상만 보여 줍니다.

다음: [제목 붙이기](05_title.md)
