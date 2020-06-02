import json
import os
from difflib import get_close_matches

import cherrypy
from kodipydent import Kodi

KODI = None


class KodiServ(object):
    try:
        os.environ["KODI_KEY"]
    except KeyError:
        cherrypy.log("KODI_KEY not set")
        key = "qZu3vhYicbJA87Xq2bofnwQMyQ"
    else:
        key = os.environ["KODI_KEY"]

    def can_request(self) -> bool:
        header = cherrypy.request.headers
        if "Auth-Key" in header.keys() and header["Auth-Key"] == self.key:
            return True
        else:
            self.auth_failed()
            return False

    @staticmethod
    def auth_failed():
        raise cherrypy.HTTPError(401, message="Authentication failed")

    # commands
    @cherrypy.expose
    def play(self, title=None, id=None):
        if self.can_request() and (title is not None or id is not None):
            movies = self.getmovies()
            # TODO comparator9000()
            for movie in movies:
                if movie["label"] == title:
                    id = movie["id"]
                    break
            KODI.Player.Open(item={"movieid": id})

    @cherrypy.expose
    def pause(self):
        if self.can_request():
            KODI.Player.PlayPause(1)

    @cherrypy.expose
    def playpause(self):
        if self.can_request():
            KODI.Player.PlayPause(1)

    @cherrypy.expose
    def stop(self):
        if self.can_request():
            KODI.Player.Stop()

    # info
    @cherrypy.expose
    def movies(self):
        movies = self.getmovies()
        fmt = "{movieid:<4} {label}\n"
        text="ID    Title\n{:-^35}\n".format("-")
        for movie in movies:
            text += fmt.format(**movie)
        return text

    @cherrypy.expose
    def nowplaying(self):
        info = KODI.Player.GetItem(playerid=1, properties=[])
        print(info)
        if info["result"]["item"]["label"] != "":
            details: dict = self.getmoviedetails(info["result"]["item"]["id"])
        else:
            details: dict = self.getmoviedetails(None)

        return json.dumps(details)

    def getmoviedetails(self, movieid) -> dict:
        fmt = {
            "active": True,
            "imdbnumber": "",
            "lastplayed": "",
            "movieid": "",
            "title": "",
            "streamdetails": "",
        }
        if movieid is None:
            fmt["title"] = "Nothing is playing"
            fmt["active"] = False
        else:
            details = KODI.VideoLibrary.GetMovieDetails(
                movieid=movieid,
                properties=["title", "imdbnumber", "lastplayed", "streamdetails"],
            )
            # AHHH FUNCTIONAL PLZ
            _ = details["result"]["moviedetails"]
            fmt["imdbnumber"] = _["imdbnumber"]
            fmt["lastplayed"] = _["lastplayed"]
            fmt["movieid"] = _["movieid"]
            fmt["title"] = _["title"]
            fmt["streamdetails"] = _["streamdetails"]
        return fmt

    def getmovies(self) -> dict:
        _ = KODI.VideoLibrary.GetMovies()
        movies = _["result"]["movies"]
        return movies

    def comparator9000(self, string: str) -> list:
        movie_list = []
        for each in movies:
            movie_list.append(each["label"])
        return get_close_matches(string, movie_list)



if __name__ == "__main__":
    config = {
        "server.socket_host": "127.0.0.1",
        "server.socket_port": 8989,
        "request.show_tracebacks": False,
        "tools.response_headers.on": True,
        "tools.response_headers.headers": [("Content-Type", "text/plain")]
    }
    cherrypy.config.update(config)
    try:
        KODI = Kodi("localhost")
    except Exception as err:
        reason = str(err.reason)
        cherrypy.log("Failed to load Kodi")
        cherrypy.log(reason)

        import sys

        sys.exit("Failed to load Kodi\n" + reason)
    else:
        try:
            cherrypy.quickstart(KodiServ())
        except Exception as err:
            sys.exit(err)
