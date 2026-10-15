<!-- AUTHOR NOTE: Every shell example indented by four spaces in the numbered files is executed by
the prysk-readme pre-commit hook, and each file runs in its own temporary directory. So each file
must be self-contained (set PROMPTQ_HOME and create its own prompt.md) and must not depend on
another file. This README holds no executable blocks. Keep the tutorial generic; concrete
integrations go under guide/cases/. -->

# 튜토리얼

CLI로 promptq를 쓰는 방법을 순서대로 익힙니다. 각 문서는 앞 문서를 읽지 않아도 따라 할 수 있도록 처음부터 시작합니다.

1. [프롬프트 넣기](01_enqueue.md)
2. [있는지 확인하기](02_has-and-list.md)
3. [가져가서 처리하기](03_claim-and-dequeue.md)
4. [오래된 claim 정리하기](04_prune-claimed.md)
5. [제목 붙이기](05_title.md)

저장소 위치는 `PROMPTQ_HOME`으로 정합니다. Producer와 Consumer가 같은 값을 써야 같은 큐를 봅니다. 설정하지 않으면 `~/.local/state/promptq`를 쓰고, `promptq home show`로 어디인지 확인할 수 있습니다. 문서의 예제는 현재 디렉터리 아래의 `queue`를 씁니다.

Python 라이브러리로 쓰려면 [how_to_use_api.py](../how_to_use_api.py)를 보세요.
