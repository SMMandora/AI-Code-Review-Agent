from codereview.diff import parse_diff, snap_line
from tests.diff_fixtures import (
    BINARY_DIFF,
    DELETED_DIFF,
    MODIFIED_DIFF,
    NEW_FILE_DIFF,
    RENAME_DIFF,
)


def test_modified_file():
    [f] = parse_diff(MODIFIED_DIFF)
    assert f.path == "app/calc.py"
    assert not f.is_new and not f.is_deleted and not f.is_binary
    assert f.commentable == frozenset({1, 2, 3, 4, 5, 6, 7, 8})
    assert "return a - b" in f.added_text
    assert "return a + b" not in f.added_text  # context/removed lines excluded
    assert f.raw.startswith("diff --git a/app/calc.py b/app/calc.py")


def test_new_file():
    [f] = parse_diff(NEW_FILE_DIFF)
    assert f.path == "app/util.py"
    assert f.is_new
    assert f.commentable == frozenset({1, 2, 3, 4, 5})


def test_deleted_file_has_no_commentable_lines():
    [f] = parse_diff(DELETED_DIFF)
    assert f.is_deleted
    assert f.commentable == frozenset()


def test_rename_uses_new_path():
    [f] = parse_diff(RENAME_DIFF)
    assert f.path == "app/after.py"
    assert f.commentable == frozenset({1, 2})


def test_binary_flagged():
    [f] = parse_diff(BINARY_DIFF)
    assert f.is_binary


def test_multi_file_diff():
    files = parse_diff(MODIFIED_DIFF + NEW_FILE_DIFF)
    assert [f.path for f in files] == ["app/calc.py", "app/util.py"]


def test_snap_exact():
    [f] = parse_diff(NEW_FILE_DIFF)
    assert snap_line(f, 2) == 2


def test_snap_nearby():
    [f] = parse_diff(NEW_FILE_DIFF)
    assert snap_line(f, 8) == 5  # distance 3 <= 5


def test_snap_too_far():
    [f] = parse_diff(NEW_FILE_DIFF)
    assert snap_line(f, 50) is None


def test_snap_deleted_file():
    [f] = parse_diff(DELETED_DIFF)
    assert snap_line(f, 1) is None
