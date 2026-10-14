# GitHub Actions가 찾은 일을 Claude 세션이 처리하기

<!-- AUTHOR NOTE: Integrations tied to a specific tool or purpose belong under guide/cases/, as short
examples of one way to use promptq. They are not executed, so keep them to commands the tutorial
covers. -->

Self-hosted Runner의 스케줄 잡(Producer)이 PR의 충돌 같은 일을 발견해 큐에 넣고, 같은 기기에서 쓰는 Claude 세션(Consumer)이 나중에 가져가 처리하는 사용 방식입니다.

- 이름을 `GITHUB/<owner>/<repo>/<종류>/<번호>`로 정하면 같은 PR은 몇 번 발견해도 한 번만 들어갑니다.
- 세션을 시작할 때 hook이 `has`로 해당 repo의 항목이 있는지만 확인하고, 있으면 별도 세션(Chip)을 제안합니다.
- 그 세션이 `claim-one`을 `status: empty`가 나올 때까지 반복해 처리합니다.
- 제목을 붙여 두면 hook이 `has`가 성공했을 때 `promptq list`의 첫 줄(다음에 가져갈 항목)에서 제목을 읽어, 띄우는 세션의 이름으로 쓸 수 있습니다.

```bash
# Producer (Actions 잡): 오래된 claim을 정리하고 새 일을 넣는다
promptq prune-claimed --matched older-than:6h
promptq enqueue --name "GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12" --title "Resolve the conflict in PR 12" \
  --file prompt.md --on-dup ignore --dup-ok

# 세션 시작 hook: 출력 없이 종료 코드만 본다
promptq has --matched "prefix:GITHUB/octocat/hello/" --quiet

# 처리하는 세션: 비어 있을 때까지 반복한다
promptq claim-one --matched "prefix:GITHUB/octocat/hello/" --empty-ok
promptq dequeue --name "GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12"
```
