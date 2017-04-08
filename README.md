# music-learning

A collection of Python scripts for clustering, sorting, and organizing playlists in various ways to optimize the listening experience.
Primarly used at http://www.aFIREintheattic.com and for the connected Spotify account https://open.spotify.com/user/kroening.

Inside:

- Airplay
  - spotifyairplay.py -- sorts a list of Spotify uris by popularity replacing explicit versions with clean versions
- Album Rating
  - rate_albums.py -- rates albums using a custom formula taking individual song ratings as input
- Cluster Playlists
  - cluster.py -- returns multiple playlists from one, clustering songs in the output by term similarity
  - sort_genre.py -- returns multiple playlists from one, clustering songs in the output by Spotify genre similarity
- DRM Removal
  - drmstrip_video.py -- DRM removal for m4v files
  - drmstrip.py -- DRM removal for m4a files
- Miscellaneous
  - album_rater.py -- rates a single album using a custom formula via command prompt of individual song ratings
  - itunes_list.py -- html formats an iTunes txt playlist file into a numbered list
  - itunes_spotify.py -- given an iTunes txt playlist file, finds all matching Spotify uris
  - numbered_list.py -- takes a newline separated file and returns a numbered html list
  - popularity.py -- sorts a list of Spotify uris by popularity
  - search_playlists.py -- given an artist name and song title, finds all of a specific user's Spotify playlist containing that song
  - shuffle.py -- randomly shuffles a list of Spotify uris
  - wp_postportfolio.py -- takes Wordpress post text, and returns a custom Wordpress portfolio format
- Modules
  - db_methods.py -- methods used to search and save databases
  - helpers.py -- file and API helper functions
  - spotify_methods.py -- Spotify-specific API and return object helper methods
- Playlist Flow
  - playlist_flow.py -- sorts a list of Spotify uris into a smooth flow given a starting song using Echonest and Spotify metadata
