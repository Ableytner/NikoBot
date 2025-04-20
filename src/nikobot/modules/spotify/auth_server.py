import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

from abllib import log, VolatileStorage

logger = log.get_logger("SpotifyAuthServer")

SERVER_ADDRESS = ("", 80)

def run_http_server(completion_func):
    """Runs the http server in an infinite loop"""

    with _HTTPServer(completion_func) as httpd:
        httpd.timeout = 30

        while True:
            if len(VolatileStorage["spotify.auth"]) > 0:
                httpd.handle_request()
            
            sleep(1)

class _HTTPServer(HTTPServer):
    def __init__(self, completion_func) -> None:
        super().__init__(SERVER_ADDRESS, _HTTPRequestHandler)
        self.completion_func = completion_func

class _HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith("/spotify_auth"):
            logger.warning(f"{self.client_address} sent unsupported request: {self.path}")
            self.close_connection = True
            self.send_response(404) # not found
            return

        url_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = url_params["code"][0]
        state = url_params["state"][0]

        for user_id, state_candidate in VolatileStorage["spotify.auth"].items():
            if state_candidate == state:
                self.close_connection = True
                self.send_response(200) # OK

                self.server.completion_func(user_id, auth_code, state)
                return

        self.close_connection = True
        self.send_response(400) # invalid request
