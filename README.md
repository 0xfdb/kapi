# Kapi
`Usage: main.py [CONFIGURATION FILE]`

Some paths are public and some require `Auth-Key` in the request header. Set with the key in `config.ini -> Server -> key`

### Things TODO
- Handle TV Shows
- Use difflib's sequencematcher to guesstimate titles
- Maybe add an additional endpoint to search, return a list

### Endpoints Requiring Auth
`/play?title=TITLE&id=ID`
`/pause`
`/playpause` (bit redundant no?)
`/stop`
### Public Endpoints
`/movies` returns an html page with a table of movies, style can be set in the `config.ini`
`/nowplaying` Returns json about the current video being played:
```json
{
  "imdbnumber": "tt0078748",
  "label": "Alien",
  "lastplayed": "2020-06-01 23:40:16",
  "movieid": 24,
  "streamdetails": {
    "audio": [
      {
        "channels": 6,
        "codec": "ac3",
        "language": "eng"
      }
    ],
    "subtitle": [
      {
        "language": "eng"
      }
    ],
    "video": [
      {
        "aspect": 2.364531993865967,
        "codec": "hevc",
        "duration": 6997,
        "height": 812,
        "language": "",
        "stereomode": "",
        "width": 1920
      }
    ]
  },
  "title": "Alien",
  "active": true
}
```
If there is no active video, `/nowplaying` returns:
```json
{"active": false, "title": "Nothing is playing"}
```
