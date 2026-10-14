"""promptq 예외. 모든 예외는 PromptqError를 상속한다 (CLI 종료 코드 매핑은 cli 모듈)."""


class PromptqError(Exception):
    """promptq가 내는 모든 예외의 기반."""


class InvalidName(PromptqError):
    """이름 또는 prefix가 형식 규칙을 어겼다."""


class NameConflict(PromptqError):
    """이름이 다른 이름의 상위 경로이거나 하위 경로라서 공존할 수 없다."""


class InvalidSelector(PromptqError):
    """selector 문법이나 사용 범위가 잘못됐다."""


class InvalidHome(PromptqError):
    """저장소 경로가 잘못됐다 (예: 상대 경로)."""


class BodyTooLarge(PromptqError):
    """본문이 상한을 넘었다."""


class StoreError(PromptqError):
    """저장소 문제."""


class IncompatibleStore(StoreError):
    """저장소가 이 버전의 promptq와 호환되지 않는다."""
