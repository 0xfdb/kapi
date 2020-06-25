"""Usage: main.py [CONFIGURATION FILE]
"""

import configparser
import json
import sys
import time
from difflib import SequenceMatcher, get_close_matches
from typing import NoReturn, Optional

import cherrypy

from kodipydent import Kodi

KODI = None


class KodiServ:
    def __init__(self, key: str, style: str):
        self.key: str = key
        self.style: str = style
        self.lastreqtime: float = time.time()
        self.lastnowplayingreq: dict = {}

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

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def search(self, title: str) -> dict:
        if self.can_request():
            toret = {"matches": []}
            movies = self.getmovies()
            matcher = SequenceMatcher(lambda _: _ in "-,", title.lower())
            for movie in movies:
                matcher.set_seq2(movie["label"].lower())
                if matcher.ratio() > 0.75:
                    print(matcher.ratio())
                    toret["matches"].append(movie)
            return toret

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
    def tvshows(self) -> str:
        tvshows = self.getshows()
        page = """
        <html><head><title>TV Show List</title>
        <style>{style}</style></head>
        <table><tr><th>ID</th><th>Title</th></tr>
        """.format(
            style=self.style
        )
        entryline = "<tr><td>{tvshowid}</td><td>{label}</td></tr>\n"
        for tvshow in tvshows:
            page += entryline.format(**tvshow)
        page += "</table>\n</html>"
        return page

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def nowplaying(self) -> dict:
        if (time.time() - self.lastreq) >= 5:
            self.lastreqtime = time.time()
            details = self.getnowplaying()
            self.lastnowplayingreq = details
            return details
        else:
            return self.lastnowplayingreq

    def getnowplaying(self) -> dict:
        info = KODI.Player.GetItem(playerid=1, properties=[])
        if info["result"]["item"]["label"] != "" and info["result"]["item"]["type"] == "movie":
            details: dict = self.getmoviedetails(info["result"]["item"]["id"])
        elif info["result"]["item"]["label"] != "" and info["result"]["item"]["type"] == "episode":
            tvshowid = KODI.Player.GetItem(playerid=1, properties=["tvshowid"])["result"]["item"]["tvshowid"]
            seasonid = KODI.VideoLibrary.GetEpisodeDetails(episodeid=tvshowid, properties=["seasonid"])["result"]["episodedetails"]["seasonid"]
            details: dict = self.getepisodedetails(info["result"]["item"]["id"],tvshowid,seasonid)
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

    def getepisodedetails(self, episodeid: str, tvshowid: str, seasonid: str) -> dict:
        if episodeid is None:
            return {"active": False, "title": "Nothing is playing"}
        else:
            show_name = KODI.VideoLibrary.GetTVShowDetails(tvshowid=tvshowid)["result"]["tvshowdetails"]["label"]
            episode_title = KODI.VideoLibrary.GetEpisodeDetails(episodeid=episodeid,)["result"]["episodedetails"]["label"]
            episode_season = KODI.VideoLibrary.GetSeasonDetails(seasonid=seasonid)["result"]["seasondetails"]["label"]
            episode_properties = KODI.VideoLibrary.GetEpisodeDetails(episodeid=episodeid, properties=["lastplayed", "streamdetails"])["result"]["episodedetails"]
            longtitle = show_name + ' ' + episode_season + ': ' + episode_title
            detail_head = {"active": True, "title": longtitle}
            details = {}
            details.update(detail_head)
            details.update(episode_properties)
        return details

    def getmovies(self) -> dict:
        query = KODI.VideoLibrary.GetMovies()
        return query["result"]["movies"]


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
            "tools.response_headers.headers": [("Access-Control-Allow-Origin", "https://0xfdb.xyz")],
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
