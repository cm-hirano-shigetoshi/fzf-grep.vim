import json
import os
import sys

import find_available_port
import internal_server


def option_to_shell_string(key, value):
    if value is None:
        return f"--{key}"
    elif isinstance(value, list):
        strs = []
        for v in value:
            assert "'" not in str(v), f"Invalid option was specified: {v}"
            strs.append(f"--{key} '{v}'")
        return " ".join(strs)
    else:
        assert "'" not in str(value), f"Invalid option was specified: {value}"
        return f"--{key} '{value}'"


def options_to_shell_string(options):
    return [option_to_shell_string(k, v) for k, v in options.items()]


def get_fzf_options_core(d, query, server_port):
    options = {
        "multi": None,
        "ansi": None,
        "query": query,
        "bind": [
            f'alt-u:execute-silent(curl "http://localhost:{server_port}?origin_move=up")',
            f'alt-p:execute-silent(curl "http://localhost:{server_port}?origin_move=back")',
            f'alt-n:execute-silent(curl "http://localhost:{server_port}?file_filter=default")',
            f'alt-l:execute-silent(curl "http://localhost:{server_port}?file_filter=uuu")',
        ],
    }
    return " ".join(options_to_shell_string(options))


def get_fzf_options_view(abs_dir):
    return f"--reverse --header '{abs_dir}' --preview 'bat --color always {{}}' --preview-window down"


def get_absdir_view(path, home_dir=os.environ["HOME"]):
    abs_dir = os.path.abspath(path)
    if abs_dir.startswith(home_dir):
        abs_dir = "~" + abs_dir[len(home_dir) :]
    if abs_dir != "/":
        abs_dir += "/"
    return abs_dir


def get_fzf_options(d, query, server_port):
    abs_dir = get_absdir_view(d)
    return " ".join(
        [
            get_fzf_options_core(d, query, server_port),
            get_fzf_options_view(abs_dir),
        ]
    )


def get_fzf_dict(d, query, server_port):
    return {"options": get_fzf_options(d, query, server_port)}


def run(origin_path, query, server_port):
    rg_command = internal_server.get_rg_command(origin_path)
    fzf_port = find_available_port.run()
    fzf_dict = get_fzf_dict(origin_path, query, server_port)
    return rg_command, fzf_dict, fzf_port


if __name__ == "__main__":
    args = sys.argv[1:]
    rg_command, fzf_dict, fzf_port = run(*args)
    print(
        json.dumps(
            {"rg_command": rg_command, "fzf_dict": fzf_dict, "fzf_port": fzf_port}
        )
    )
