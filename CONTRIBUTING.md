<!-- AUTHOR NOTE: The reader of this file is someone who changes promptq's code (maintainers and
contributors, including coding agents). It covers setup, checks, and how work is submitted.
Release steps live as a comment in pyproject.toml next to the version configuration. -->

# 기여하기

## 개발 환경

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

## 검사

CI와 같은 검사를 로컬에서 모두(테스트 포함) 실행합니다.

```bash
uv run pre-commit run --all-files --hook-stage manual
```

## PR

- 작은 PR을 쌓아서(stacked) 제출합니다. 각 PR은 CI에서 혼자 통과해야 합니다.
- PR은 squash merge하므로 PR당 커밋은 하나로 정리합니다.
- 커밋 메시지(와 PR 제목)는 [Git 커밋 메시지 규칙](https://cbea.ms/git-commit/)을 따릅니다: 영어 명령형, 제목 50자 이내, 대문자로 시작하고 마침표 없음, 본문에는 what과 why를 72자 폭으로 씁니다.
