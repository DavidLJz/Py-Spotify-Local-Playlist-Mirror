import argparse
from json import dumps
import functions
from os import path
from decouple import config

def get_spotify_trackdict(playlist:dict):
    tracklist = None

    if 'tracks' in playlist:
        if 'items' in playlist['tracks']:
            if len(playlist['tracks']['items']) > 0:
                tracklist = playlist['tracks']['items']

    if tracklist is None:
        raise Exception('No tracks found in playlist')

    trackdict = {}

    for i in range(len(tracklist)):
        t = tracklist[i]

        artists = []

        for a in t['artists']:
            artists.append(a['name'])

        tdata = {
            'id': t['id'],
            'name': t['name'],
            'album': t['album']['name'],
            'artists': artists,
            'duration_s': t['duration_ms'] / 1000,
            'position': i
        }

        trackdict[ t['id'] ] = tdata

    return trackdict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mirror a Spotify playlist to a m3u8 playlist file with local tracks')
    
    parser.add_argument('playlist_id', help='Spotify Playlist ID to mirror')
    parser.add_argument('source_dir', help='The source directory to search for tracks (including subdirectories)')
    parser.add_argument('-o', '--output', help='The full output file path, if not given will save to current directory as $playlist_id.m3u8. Cover image will be downloaded to the same directory.', default='')

    # parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    # parser.add_argument('-e', '--extensions', help='The extensions to search for', default='mp3,wav,flac')
    # parser.add_argument('-i', '--ignore', help='Ignore tracks that are not found in the source directory', action='store_true', default=False')
    parser.add_argument('-t', '--title', help='The title of the playlist, if not given will use the Spotify given name', default='')
    parser.add_argument('-c', '--cover', help='The cover image of the playlist, if not given will download and use the Spotify cover', default='')

    args = parser.parse_args()
    
    # Get the spotify playlist
    sp = functions.get_spotify_helper(
        client_id=config('SPOTIFY_CLIENT_ID'),
        client_secret=config('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=config('SPOTIFY_REDIRECT_URI'),
        scope='user-library-read,playlist-read-private,playlist-read-collaborative'
    )

    playlist = functions.get_spotify_playlist(args.playlist_id, sp)

    if playlist is None:
        print('No playlist found')
        exit(1)

    spotify_trackdict = get_spotify_trackdict(playlist)

    # Get the local tracklist
    tracklist = functions.local_tracklist_from_spotify_tracklist(spotify_trackdict, args.source_dir)

    if len(tracklist) == 0:
        print('No tracks found in playlist')
        exit(1)

    pathlist = [t['path'] for t in tracklist]

    # Save the playlist as m3u8
    title = args.title or playlist['name']
    logo = args.cover or playlist['images'][0]['url']
    output = path.abspath(args.output or f'{args.playlist_id}.m3u8')

    image_output_dir = path.dirname(output)

    if logo.startswith('http'):
        try:
            logo = functions.download_image(logo, image_output_dir)
        except Exception as e:
            print(f'Error downloading cover image: {e}')
            logo = ''

    functions.save_playlist_to_m3u8(output, pathlist, logo, title)

    n_spotify_tracks = len(spotify_trackdict)
    n_playlist = len(pathlist)

    s = f'Playlist "{title}" saved to "{output}" with {n_playlist}/{n_spotify_tracks} tracks'
    print(s)