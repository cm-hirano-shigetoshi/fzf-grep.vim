import create_fzf_command
import fzf_grep
import internal_server
import pytest


@pytest.mark.parametrize(
    "d,home,expected",
    [
        ("/Users/sample.user/aaa", "/Users/sample.user", "~/aaa/"),
        ("/absolute/path", "/Users/sample.user", "/absolute/path/"),
    ],
)
def test_get_absdir_view(d, home, expected):
    response = create_fzf_command.get_absdir_view(d, home_dir=home)
    assert response == expected


@pytest.mark.parametrize(
    "d,expected", [(".", ".."), ("/Users", "/"), ("/", "/"), ("test", ".")]
)
def test_get_parent_dir(d, expected):
    response = internal_server.get_parent_dir(d)
    assert response == expected


@pytest.mark.parametrize(
    "b,c,expected",
    [("aaa/bbbccc", 7, ("aaa", "bbb")), ("ls aaa/bbbccc", 10, ("aaa", "bbb"))],
)
def test_get_origin_path_query(b, c, expected):
    response = fzf_grep.get_origin_path_query(b, c)
    assert response == expected


@pytest.mark.parametrize(
    "d,expected",
    [
        (".", "rg --color always --line-number ^ ."),
    ],
)
def test_get_rg_command(d, expected):
    response = internal_server.get_rg_command(d)
    assert response == expected


@pytest.mark.parametrize(
    "key,value,expected",
    [
        (
            "key",
            None,
            "--key",
        ),
        (
            "key",
            123,
            "--key '123'",
        ),
        (
            "key",
            ["abc", "def"],
            "--key 'abc' --key 'def'",
        ),
    ],
)
def test_option_to_shell_string(key, value, expected):
    response = create_fzf_command.option_to_shell_string(key, value)
    assert response == expected


@pytest.mark.parametrize(
    "abs_dir,expected",
    [
        (
            "/absolute/path/",
            "--reverse --header '/absolute/path/' --delimiter ':' --preview 'bat --color always --highlight-line {2} {1}' --preview-window 'down' --preview-window '+{2}'",
        ),
        (
            "/",
            "--reverse --header '/' --delimiter ':' --preview 'bat --color always --highlight-line {2} {1}' --preview-window 'down' --preview-window '+{2}'",
        ),
    ],
)
def test_get_fzf_options_view(abs_dir, expected):
    response = create_fzf_command.get_fzf_options_view(abs_dir)
    assert response == expected


@pytest.mark.parametrize(
    "b,c,expected",
    [
        ("aaabbb", 3, ""),
        ("aaa bbb", 3, ""),
        ("aaa bbb", 4, "aaa "),
        ("aaa/bbbccc", 7, ""),
    ],
)
def test_get_left(b, c, expected):
    response = fzf_grep.get_left(b, c)
    assert response == expected


@pytest.mark.parametrize(
    "b,c,expected",
    [
        ("aaabbb", 3, "bbb"),
        ("aaa bbb", 3, " bbb"),
        ("aaa bbb", 4, "bbb"),
        ("aaa/bbbccc", 7, "ccc"),
    ],
)
def test_get_right(b, c, expected):
    response = fzf_grep.get_right(b, c)
    assert response == expected


@pytest.mark.parametrize(
    "b,c,items,expected",
    [
        ("aaabbb", 3, "select1\nselect2\n", "select1 select2 bbb"),
        ("ls test/abbb", 9, "select1\nselect2\n", "ls select1 select2 bbb"),
    ],
)
def test_get_buffer_from_items(b, c, items, expected):
    response = fzf_grep.get_buffer_from_items(b, c, items)
    assert response == expected


@pytest.mark.parametrize(
    "b,c,items,expected",
    [
        ("aaabbb", 3, "select1\nselect2\n", 16),
        ("ls test/abbb", 9, "select1\nselect2\n", 19),
    ],
)
def test_get_cursor_from_items(b, c, items, expected):
    response = fzf_grep.get_cursor_from_items(b, c, items)
    assert response == expected
