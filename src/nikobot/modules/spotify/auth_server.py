"""
Module which contains an http server for spotify OAuth

See https://developer.spotify.com/documentation/web-api/tutorials/code-flow for more details
"""

import asyncio
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from time import sleep

from abllib import log, VolatileStorage

from . import auth_helper
from ...util import general

logger = log.get_logger("spotify.auth_server")

SERVER_ADDRESS = ("", 80)

def run_http_server():
    """Runs the http server in an infinite loop"""

    with _HTTPServer() as httpd:
        httpd.timeout = 30

        while True:
            if "spotify.auth" in VolatileStorage and len(VolatileStorage["spotify.auth"]) > 0:
                httpd.handle_request()

            sleep(1)

class _HTTPServer(HTTPServer):
    """Modified version of http.server.HTTPServer"""

    def __init__(self) -> None:
        super().__init__(SERVER_ADDRESS, _HTTPRequestHandler)

class _HTTPRequestHandler(BaseHTTPRequestHandler):
    """Modified version of http.server.BaseHTTPRequestHandler"""

    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.close_connection = True

    def do_GET(self):
        """Define behaviour if an GET request is received"""

        if not self.path.startswith("/spotify_auth"):
            logger.warning(f"{self.client_address} sent unsupported request: {self.path}")
            self.respond(404, "Address not found.") # not found
            return

        url_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        state = url_params["state"][0]

        user_id = None
        for u_id, state_candidate in VolatileStorage["spotify.auth"].items():
            if state_candidate == state:
                user_id = u_id

        if user_id is None:
            self.respond(400, "Invalid authentication state. Maybe you waited too long?") # invalid request
            return

        if "error" in url_params and url_params["error"][0] == "access_denied":
            # user cancelled auth
            auth_helper.cancel_auth(user_id)
            self.respond(400, "Registration was cancelled by user.") # access was denied
            return

        auth_code = url_params["code"][0]
        general.sync(auth_helper.complete_auth(user_id, auth_code))
        self.respond(200, "Your Spotify account was successfully registered with the NikoBot discord bot.") # OK

    def respond(self, code: int, message: str) -> None:
        """Send a response to the client"""

        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        html = f"<html><body><h1>{message}</h1></body></html>"
        self.wfile.write(html.encode("utf8"))

    def log_request(self, code = "-", size = "-"):
        pass
