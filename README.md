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

## 빠르게 써 보기

<!-- AUTHOR NOTE: Keep this to the smallest CLI flow (enqueue, claim-one, dequeue). Every shell
example indented by four spaces is executed by the prysk-readme pre-commit hook. Anything longer
belongs under guide/. -->

저장소 위치는 `PROMPTQ_HOME`으로 정합니다. Producer와 Consumer가 같은 값을 써야 같은 큐를 봅니다.

    $ export PROMPTQ_HOME="$PWD/queue"
    $ echo '이 문서를 세 줄로 요약해 주세요.' > prompt.md
    $ promptq enqueue --name myapp/SUMMARIZE/1 --file prompt.md --on-dup ignore
    $ promptq claim-one --matched prefix:myapp/
    status: claimed
    name: myapp/SUMMARIZE/1
    ---
    이 문서를 세 줄로 요약해 주세요.
    $ promptq dequeue --name myapp/SUMMARIZE/1

## 더 알아보기

<!-- AUTHOR NOTE: The README is deliberately short; the detailed material lives under guide/.
Target layout:
  guide/tutorial/README.md      table of contents for the numbered CLI tutorial
  guide/tutorial/NN_<slug>.md   one step per file; each is self-contained and run by prysk
  guide/how_to_use_api.py       Python API example, run by the example-api hook
  guide/cases/<slug>.md         integrations tied to a specific tool (not executed)
Why it looks like this today: there is only one case, so it is linked directly instead of through
guide/cases/README.md. When a second case is added, create guide/cases/README.md as an index and
link the directory here instead. If you add a tutorial step, also add it to
guide/tutorial/README.md. The prysk-readme hook covers README.md and guide/tutorial/[0-9]*.md, so
a new numbered tutorial file is picked up by its glob; files outside it are not tested. -->

- [튜토리얼](guide/tutorial/): CLI 사용법을 단계별로 익힙니다.
- [Python API](guide/how_to_use_api.py): 넣기, 가져가기, 지우기를 라이브러리로 해 보는 예제입니다. 저장소를 clone한 뒤 `PROMPTQ_HOME="$(mktemp -d)/queue" uv run python guide/how_to_use_api.py`로 실행해 보세요.
- 사례: [GitHub Actions가 찾은 일을 Claude 세션이 처리하기](guide/cases/github-actions-claude.md)
- 개발에 참여하려면 [CONTRIBUTING.md](CONTRIBUTING.md)를 보세요.
