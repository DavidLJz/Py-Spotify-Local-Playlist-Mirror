from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

class SpotipyHelper:
  def __init__(
    self, client_id:str, client_secret:str, redirect_uri:str, scope:str, requests_timeout:int=5
    ) -> None:

    self._sp = Spotify(auth_manager=SpotifyOAuth(
      client_id=client_id,
      client_secret=client_secret,
      redirect_uri=redirect_uri,
      scope=scope,
      requests_timeout=requests_timeout
      )
    )

  def my_saved_tracks(self, limit:int=20, offset:int=0):
    return self._sp.current_user_saved_tracks(limit=limit, offset=offset)

  def my_playlists(self, limit:int=20, offset:int=0):
    return self._sp.current_user_playlists(limit=limit, offset=offset)

  def playlist_by_id(self, id:str, fields=None):
    return self._sp.playlist(id, fields=fields)

  def get_spotify_playlist_tracks(self, id:str, fields=None, limit:int=20, offset:int=0):
    return self._sp.playlist_tracks(id, fields=fields, limit=limit, offset=offset)