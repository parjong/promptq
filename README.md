<!-- AUTHOR NOTE: The reader of this file is someone who *uses* promptq (someone writing a Producer
that enqueues prompts, or a Consumer that claims and handles them). Development and release
procedures do not belong here: see CONTRIBUTING.md and the comments in pyproject.toml. -->

# promptq

한 기기 안에서 프로세스 사이에 프롬프트를 넘겨주는 작은 로컬 대기열입니다.

- **Producer**는 이름을 붙여 프롬프트를 넣습니다. 같은 이름이 이미 있을 때의 동작을 지정할 수 있어서, 같은 작업을 몇 번 실행해도 안전합니다.
- **Consumer**는 프롬프트를 하나씩 가져가(claim) 처리하고, 끝나면 지웁니다. 여러 Consumer가 동시에 가져가도 항목마다 정확히 한 명만 받습니다.
- 서버나 데몬 없이 로컬 디렉터리만 쓰고, CLI와 Python 라이브러리로 쓸 수 있습니다.

## 상태

<!-- AUTHOR NOTE: TODO: replace this section with a short usage tutorial when the CLI lands. -->

개발 중입니다. 아직 사용할 수 있는 CLI와 API가 없습니다. 사용법은 CLI가 들어올 때 이 문서에 추가됩니다.

개발에 참여하려면 [CONTRIBUTING.md](CONTRIBUTING.md)를 보세요.
