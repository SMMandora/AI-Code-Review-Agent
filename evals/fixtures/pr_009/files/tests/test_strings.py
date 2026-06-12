from app.strings import slugify, truncate


def test_truncate_short():
    assert truncate("hi", 80) == "hi"


def test_truncate_long():
    assert truncate("x" * 100, 80).endswith("...")


def test_slugify():
    assert slugify("Hello World!") == "hello-world"
