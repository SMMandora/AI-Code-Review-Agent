_CACHE: dict = {}


def get(key: str, seen: list = []) -> object:
    if key in seen:
        return None
    seen.append(key)
    return _CACHE.get(key)
