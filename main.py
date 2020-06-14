"""Usage: main.py [CONFIGURATION FILE]
"""

import configparser
import json
import sys
from difflib import get_close_matches
from typing import NoReturn, Optional

import cherrypy

from kodipydent import Kodi

KODI = None


class KodiServ:
    def __init__(self, key: str, style: str):
        self.key: str = key
        self.style: str = style

    def can_request(self) -> bool:
        header = cherrypy.request.headers
        if "Auth-Key" in header.keys() and header["Auth-Key"] == self.key:
            return True
        else:
            self.auth_failed()
            return False

    @staticmethod
    def auth_failed() -> NoReturn:
        raise cherrypy.HTTPError(401, message="Authentication failed")

    # commands
    @cherrypy.expose
    def play(self, title: Optional[str] = None, id: Optional[int] = None) -> NoReturn:
        if self.can_request() and (title is not None or id is not None):
            movies = self.getmovies()
            # TODO comparator9000()
            for movie in movies:
                if movie["label"] == title:
                    id = movie["id"]
                    break
            KODI.Player.Open(item={"movieid": id})

    @cherrypy.expose
    def pause(self) -> NoReturn:
        if self.can_request():
            KODI.Player.PlayPause(1)

    @cherrypy.expose
    def playpause(self) -> NoReturn:
        if self.can_request():
            KODI.Player.PlayPause(1)

    @cherrypy.expose
    def stop(self) -> NoReturn:
        if self.can_request():
            KODI.Player.Stop()

    # info
    @cherrypy.expose
    def movies(self) -> str:
        movies = self.getmovies()
        page = """
        <html><head><title>Movie List</title>
        <style>{style}</style></head>
        <table><tr><th>ID</th><th>Title</th></tr>
        """.format(
            style=self.style
        )
        entryline = "<tr><td>{movieid}</td><td>{label}</td></tr>\n"
        for movie in movies:
            page += entryline.format(**movie)
        page += "</table>\n</html>"
        return page

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def nowplaying(self) -> str:
        info = KODI.Player.GetItem(playerid=1, properties=[])
        if info["result"]["item"]["label"] != "":
            details: dict = self.getmoviedetails(info["result"]["item"]["id"])
        else:
            details: dict = self.getmoviedetails(None)

        return details

    def getmoviedetails(self, movieid: str) -> dict:
        if movieid is None:
            return {"active": False, "title": "Nothing is playing"}
        else:
            details = KODI.VideoLibrary.GetMovieDetails(
                movieid=movieid,
                properties=["title", "imdbnumber", "lastplayed", "streamdetails"],
            )
            details["result"]["moviedetails"]["active"] = True
        return details["result"]["moviedetails"]

    def getmovies(self) -> dict:
        query = KODI.VideoLibrary.GetMovies()
        return query["result"]["movies"]

    def comparator9000(self, string: str) -> list:
        movie_list = []
        for each in movies:
            movie_list.append(each["label"])
        return get_close_matches(string, movie_list)


if __name__ == "__main__":
    try:
        kapiconfig = sys.argv[1]
    except IndexError:
        print("Missing configuration file")
        sys.exit(__doc__)
    else:
        config = configparser.ConfigParser()
        config.read(kapiconfig)
        cherrypyconfig = {
            "server.socket_host": config["Server"]["host"],
            "server.socket_port": config.getint("Server", "port"),
            "request.show_tracebacks": config.getboolean(
                "Server", "debug", fallback=False
            ),
            "tools.response_headers.on": True,
            "tools.response_headers.headers": [("Content-Type", "text/html")],
        }
        cherrypy.config.update(cherrypyconfig)
    try:
        KODI = Kodi(
            hostname=config["Kodi"]["hostname"],
            port=config["Kodi"]["port"],
            username=config.get("Kodi", "username", fallback=None),
            password=config.get("Kodi", "password", fallback=None),
        )
    except Exception as err:
        cherrypy.log(str(err.reason))
        sys.exit(f"Failed to load Kodi\n{str(err.reason)}")
    else:
        style = config.get("Server", "style")
        cherrypy.quickstart(KodiServ(key=config["Server"]["key"], style=style))
