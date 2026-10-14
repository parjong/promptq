# promptq

외부 프로세스(예: GitHub Actions Self-hosted Runner)가 만든 프롬프트를, 같은 기기에서 동작하는 Claude 세션이 나중에 가져가 처리할 수 있게 해주는 로컬 대기열.

## 개발

```bash
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
uv run pre-commit run --all-files
uv run mypy
uv run pytest
```

## 버전

버전은 git 태그에서 자동으로 정해집니다 (hatch-vcs). 코드에 버전을 적지 않습니다. 릴리스는 태그만 찍으면 됩니다.

```bash
git tag v0.1.0 && git push origin v0.1.0
```
