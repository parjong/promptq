<!-- AUTHOR NOTE: The reader of this file is someone who *uses* promptq (someone writing a Producer
that enqueues prompts, or a Consumer that claims and handles them). Development and release
procedures do not belong here: see CONTRIBUTING.md and the comments in pyproject.toml. -->

# promptq

한 기기 안에서 프로세스 사이에 프롬프트를 넘겨주는 작은 로컬 대기열입니다.

- **Producer**는 이름을 붙여 프롬프트를 넣습니다. 같은 이름이 이미 있을 때의 동작을 지정할 수 있어서, 같은 작업을 몇 번 실행해도 안전합니다.
- **Consumer**는 프롬프트를 하나씩 가져가(claim) 처리하고, 끝나면 지웁니다. 여러 Consumer가 동시에 가져가도 항목마다 정확히 한 명만 받습니다.
- 서버나 데몬 없이 로컬 디렉터리만 쓰고, CLI와 Python 라이브러리로 쓸 수 있습니다.

## 설치

```bash
uv tool install git+https://github.com/parjong/promptq   # CLI
uv add git+https://github.com/parjong/promptq            # 프로젝트의 라이브러리
```

## 튜토리얼

<!-- AUTHOR NOTE: Every shell example indented by four spaces is executed by the prysk-readme
pre-commit hook. Keep examples runnable and keep prose out of the indented blocks. Python
examples are real files under examples/, run by the example-api hook, not embedded here. Keep
the tutorial generic; concrete integrations go under "사례". -->

저장소 위치는 `PROMPTQ_HOME`으로 정합니다. Producer와 Consumer가 같은 값을 써야 같은 큐를 봅니다. 설정하지 않으면 `~/.local/state/promptq`를 쓰고, `promptq home show`로 어디인지 확인할 수 있습니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ promptq home show --explain | sed "s#$PWD#.#"
    path: ./queue
    source: PROMPTQ_HOME
    exists: no

### 1. 프롬프트 넣기

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

### 2. 있는지 확인하기

`has`는 아무것도 출력하지 않고 종료 코드로만 답합니다. 자주 불러도 부담이 없습니다. `prefix:`는 글자 그대로 비교하므로 칸 경계인 `/`로 끝내세요. `list`는 상태와 이름을 보여 주고, 언제 그 상태가 되었는지 알고 싶으면 `--show-time`을 붙이세요.

    $ promptq has --matched prefix:myapp/
    $ promptq has --matched prefix:other/
    [1]
    $ promptq list
    pending myapp/SUMMARIZE/1

### 3. 가져가서 처리하기

`claim-one`은 가장 오래된 프롬프트를 하나 가져갑니다. 첫 줄은 항상 `status: claimed` 또는 `status: empty`이고, `---` 아래는 본문 그대로입니다. (가져간 시각은 `--show-time`을 붙이면 `claimed_at:` 줄로 나옵니다.)

    $ promptq claim-one --matched prefix:myapp/
    status: claimed
    name: myapp/SUMMARIZE/1
    ---
    이 문서를 세 줄로 요약해 주세요.

처리가 끝나면 `dequeue`로 지웁니다. 처리할 수 없으면 `release`로 큐에 돌려놓습니다.

    $ promptq dequeue --name myapp/SUMMARIZE/1

더 가져갈 것이 없으면 종료 코드 1을 돌려줍니다. 종료 코드 1을 실패로 받아들이는 호출자는 `--empty-ok`로 0을 받으세요.

    $ promptq claim-one --matched prefix:myapp/
    status: empty
    [1]
    $ promptq claim-one --matched prefix:myapp/ --empty-ok
    status: empty

### 4. 오래된 claim 정리하기

Consumer가 죽으면 claim된 항목이 남습니다. Producer가 새로 넣기 전에 정리하세요. `older-than:`은 단위(`s`, `m`, `h`, `d`)가 필수이고, 처리 시간보다 충분히 길게 잡습니다.

    $ promptq prune-claimed --matched older-than:6h --matched prefix:myapp/

`--dry-run`을 붙이면 지우지 않고 대상만 보여 줍니다.

## Python API

CLI와 같은 동작을 라이브러리로 쓸 수 있습니다. 넣기, 가져가기, 지우기를 한 번씩 해 보는 예제는 [examples/how_to_api.py](examples/how_to_api.py)에 있습니다. 저장소를 clone한 뒤 임시 디렉터리를 큐로 삼아 실행해 보세요.

```bash
PROMPTQ_HOME="$(mktemp -d)/queue" uv run python examples/how_to_api.py
```

## 사례

<!-- AUTHOR NOTE: Integrations tied to a specific tool or purpose belong here, as short examples
of one way to use promptq. They are not executed, so keep them to commands the tutorial covers. -->

### GitHub Actions가 찾은 일을 Claude 세션이 처리하기

Self-hosted Runner의 스케줄 잡(Producer)이 PR의 충돌 같은 일을 발견해 큐에 넣고, 같은 기기에서 쓰는 Claude 세션(Consumer)이 나중에 가져가 처리하는 사용 방식입니다.

- 이름을 `GITHUB/<owner>/<repo>/<종류>/<번호>`로 정하면 같은 PR은 몇 번 발견해도 한 번만 들어갑니다.
- 세션을 시작할 때 hook이 `has`로 해당 repo의 항목이 있는지만 확인하고, 있으면 별도 세션(Chip)을 제안합니다.
- 그 세션이 `claim-one`을 `status: empty`가 나올 때까지 반복해 처리합니다.

```bash
# Producer (Actions 잡): 오래된 claim을 정리하고 새 일을 넣는다
promptq prune-claimed --matched older-than:6h
promptq enqueue --name "GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12" --file prompt.md --on-dup ignore --dup-ok

# 세션 시작 hook: 출력 없이 종료 코드만 본다
promptq has --matched "prefix:GITHUB/octocat/hello/" --quiet

# 처리하는 세션: 비어 있을 때까지 반복한다
promptq claim-one --matched "prefix:GITHUB/octocat/hello/" --empty-ok
promptq dequeue --name "GITHUB/octocat/hello/RESOLVE_PR_CONFLICT/12"
```

## 더 알아보기

개발에 참여하려면 [CONTRIBUTING.md](CONTRIBUTING.md)를 보세요.
