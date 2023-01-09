import argparse
from decouple import config
from functions import get_spotify_helper
from json import dumps

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Prints your playlists')
    
    args = parser.parse_args()

    # Get the spotify playlist
    sp = get_spotify_helper(
        client_id=config('SPOTIFY_CLIENT_ID'),
        client_secret=config('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=config('SPOTIFY_REDIRECT_URI'),
        scope='user-library-read,playlist-read-private,playlist-read-collaborative'
    )

    playlists = sp.my_playlists(limit=50)

    print(dumps(playlists, indent=2))