import atexit
import os
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

import create_fzf_command

RG = os.environ.get("FZF_FILE_SELECTOR_RG", "rg")

fzf_port_ = -1

search_origins = []
file_filter_ = "default"


def set_fzf_port(fzf_port):
    global fzf_port_
    fzf_port_ = fzf_port
    return True


def get_rg_command(d, file_filter=None):
    file_filter = file_filter if file_filter else file_filter_

    commands = []
    commands.append(RG)
    commands.append(get_file_filter_option(file_filter))
    commands.append("--color always")
    commands.append("--line-number")
    commands.append("^")
    commands.append(d)

    return " ".join([x for x in commands if len(x) > 0])


def get_file_filter_option(file_filter):
    assert file_filter in ("default", "uuu")
    if file_filter == "default":
        return ""
    elif file_filter == "uuu":
        return "-uuu"
    else:
        return f"--{file_filter}"


def get_parent_dir(d):
    if d.startswith("/"):
        # absolute path
        return os.path.abspath(os.path.dirname(d))
    else:
        # relative path
        return os.path.relpath(f"{d}/..")


def get_fzf_api_url():
    return f"http://localhost:{fzf_port_}"


def post_to_localhost(*args, **kwargs):
    requests.post(*args, **kwargs, proxies={"http": None})


def update_file_filter(file_filter):
    global file_filter_
    file_filter_ = file_filter


def update_search_origins(move):
    if move == "up":
        if os.path.abspath(search_origins[-1]) != "/":
            search_origins.append(get_parent_dir(search_origins[-1]))
            return True
    elif move == "back":
        if len(search_origins) > 1:
            search_origins.pop(-1)
            return True
    return False


def get_origin_move_command(d):
    return f"reload({get_rg_command(d)})+change-header({create_fzf_command.get_absdir_view(d)})"


def get_file_filter_command(file_filter):
    return f"reload({get_rg_command(search_origins[-1], file_filter=file_filter)})"


def request_to_fzf(params):
    try:
        if "origin_move" in params:
            move = params["origin_move"][0]
            succeeded = update_search_origins(move)
            if succeeded:
                command = get_origin_move_command(search_origins[-1])
                post_to_localhost(get_fzf_api_url(), data=command)
                return True
        elif "file_filter" in params:
            file_filter = params["file_filter"][0]
            update_file_filter(file_filter)
            command = get_file_filter_command(file_filter)
            post_to_localhost(get_fzf_api_url(), data=command)
        return True
    except Exception as e:
        print(e, file=sys.stderr)
        return False


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)
        if "set_fzf_port" in params:
            succeeded = set_fzf_port(int(params["set_fzf_port"][0]))
        else:
            succeeded = request_to_fzf(params)
        if succeeded:
            self.send_response(200)
            self.end_headers()

    def log_message(self, format, *args):
        # supress any log messages
        return


class ThreadedHTTPServer(threading.Thread):
    def bind_socket(self):
        self.httpd = HTTPServer(("", 0), RequestHandler)
        return self.httpd.server_port

    def run(self):
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()


def start_server():
    server = ThreadedHTTPServer(daemon=True)
    port = server.bind_socket()
    atexit.register(server.stop)
    server.start()
    return port


def run_as_thread(origin_path):
    port = start_server()

    search_origins.append(origin_path)
    update_file_filter("default")

    return port


def run(origin_path, server_port, fzf_port):
    search_origins.append(origin_path)
    update_file_filter("default")

    HTTPServer(("", int(server_port)), RequestHandler).serve_forever()
    set_fzf_port(fzf_port)


if __name__ == "__main__":
    args = sys.argv[1:]
    run(*args)
