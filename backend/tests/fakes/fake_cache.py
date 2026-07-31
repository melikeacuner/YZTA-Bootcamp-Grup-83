class FakeCache:
    """Redis benzeri async get/set arayuzunu in-memory sozlukle simule eder."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self.get_calls: list[str] = []
        self.set_calls: list[tuple[str, str, int]] = []

    async def get(self, key: str) -> str | None:
        self.get_calls.append(key)
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self.set_calls.append((key, value, ex))
        self._store[key] = value
