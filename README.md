# promptq

외부 프로세스(예: GitHub Actions Self-hosted Runner)가 만든 프롬프트를, 같은 기기에서 동작하는 Claude 세션이 나중에 가져가 처리할 수 있게 해주는 로컬 대기열.

설계 문서: [parjong/personal#2323](https://github.com/parjong/personal/pull/2323)

## 개발

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run mypy
uv run pytest
```
