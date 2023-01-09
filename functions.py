import classes
import os
from tinytag import TinyTag
from warnings import warn
import requests

def get_spotify_helper(client_id:str, client_secret:str, redirect_uri:str, scope:str, timeout:int=5):
    return classes.SpotipyHelper(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        requests_timeout=timeout
    )

def get_spotify_playlist(id:str, spotipy:classes.SpotipyHelper):
    fields = "id,name,external_urls,images,tracks(total)"

    r = spotipy.playlist_by_id(id, fields=fields)
    
    if r is None:
        return None

    if r['tracks']['total'] == 0:
        return r

    r['tracks']['items'] = []

    fields = "items(track(id,name,album.name,artists(name),duration_ms))"

    offset = 0

    for i in range(r['tracks']['total']):
        tr = spotipy.get_spotify_playlist_tracks(id, fields=fields, limit=50, offset=offset)

        if tr is None or 'items' not in tr or len(tr['items']) == 0:
            break

        for t in tr['items']:
            item = t['track']

            r['tracks']['items'].append(item)

        offset = offset + (50 * i)

    return r

def get_files_with_extensions(s_dir:str, extensions:list|str):
	filelist = []

	dir_walk = os.walk(s_dir)

	for root, dirs, files in dir_walk:
		for f in files:
			ext = os.path.splitext(f)[1] or None

			if ext is None or ext not in extensions:
				continue

			filelist.append( os.path.join(root, f) )

	return filelist

def get_tracks_in_dir(s_dir:str, extensions:list|str=""):
    '''
    Gets all audio file in a directory and all subdirectories
    '''

    if len(extensions) == 0:
        extensions = '.mp3,.flac,.wav'

    files = get_files_with_extensions(s_dir, extensions=extensions)

    tracklist = []

    for f in files:
        tags = TinyTag.get(f)

        if tags.title is None:
            continue

        d = tags.as_dict()
        d['path'] = f

        tracklist.append(d)

    return tracklist

def get_albums_in_dir(s_dir:str, lowercase:bool=False):
    '''
    Returns a dictionary where each index is an artist + album string and its value is a dict of album info
    '''

    tracks = get_tracks_in_dir(s_dir=s_dir)

    albums_dict = {}

    for t in tracks:
        artist = str(t['albumartist'] or t['artist'] or "").strip()
        album_title = str(t['album'] or "").strip()

        s_id = ""

        if artist == "" and album_title == "":
            s_id = "Unknown"
        else:
            s_id = " - ".join([s for s in [artist, album_title] if s])

        if lowercase is True:
            s_id = s_id.lower()

        if s_id not in albums_dict:
            albums_dict[ s_id ] = {
                "title": album_title,
                "artist": artist,
                "tracks": []
            }
        
        albums_dict[ s_id ]['tracks'].append(t)

    return albums_dict

def album_dict_from_spotify_tracklist(spotify_tracks:dict):
    '''
    Returns a dictionary where each index is an artist + album string and its 
    value is an array of track ids that belong to that album
    '''

    albums = {}

    for s_id in spotify_tracks:
        t = spotify_tracks[ s_id ]

        album = t['album']

        for artist in t['artists']:
            s_album_id = artist + ' - ' + album

            if s_album_id not in albums:
                albums[ s_album_id ] = []

            albums[ s_album_id ].append(s_id)

    return albums

def find_local_files_from_spotify_tracklist(spotify_tracks:dict, s_dir:str):
    '''
    Looks for local files that match against each of the tracks in a given spotify_track dict

    The algorithm for local file lookup is the following:
    1. Find all the audio files in given directory and get metadata for each
    2. Group them by artist and album in a dictionary
    3. Compare said album dict against an album dict built from the given spotify tracks
    
    '''

    spotify_albums = album_dict_from_spotify_tracklist(spotify_tracks)

    local_albums = get_albums_in_dir(s_dir, True)

    for album in spotify_albums:
        if album.lower() not in local_albums:
            continue

        local_album_tracklist = local_albums[ album.lower() ]['tracks']

        for track_id in spotify_albums[ album ]:
            spt_title = spotify_tracks[ track_id ]['name'].lower()

            if 'files' not in spotify_tracks[ track_id ]:
                spotify_tracks[ track_id ]['files'] = []

            for local_track in local_album_tracklist:
                lt_title = str(local_track['title'] or "").strip().lower()

                if lt_title != spt_title:
                    continue

                spotify_tracks[ track_id ]['files'].append(local_track)

    return spotify_tracks

def local_track_choice(files:list, name:str):
    '''
    Prompts the user to make a choice
    '''

    print(f"Track {name} has multiple local files, choose one\n")

    s_prompt = ''

    filerange = range(len(files))

    for i in filerange:
        idx = i+1

        f = files[i]

        ftitle = f['title']
        fpath = f['path']
        fbitrate = int(f['bitrate'])
        
        s_prompt += f'{idx} - {ftitle} {fbitrate}kps | {fpath}\n'

    s_choice = input(s_prompt)

    while s_choice.isnumeric() is False or int(s_choice) not in filerange:
        print("Option given not valid. Choose from these\n")

        s_choice = input(s_prompt)

    i_choice = int(s_choice)

    return files[i_choice]

def local_tracklist_from_spotify_tracklist(spotify_tracks:dict, s_dir:str) -> list:
    '''
    Returns a list of local tracks that match a given spotify tracklist
    '''

    result = find_local_files_from_spotify_tracklist(spotify_tracks, s_dir)

    print("Building playlist...")

    tracklist = []

    for s_id in result:
        track = result[s_id]

        files = []

        if 'files' in track:
            files = track['files']

        name = track['name']

        if len(files) == 0:
            print("No local files found for track: ", name)
            continue

        if len(files) == 1:
            track = files[0]
        else:
            track = local_track_choice(files, name)

        tracklist.append(track)

    return tracklist

def playlist_to_m3u8(tracklist:list, logo:str="", title:str="", start_path="") -> bytes:
    if len(tracklist) == 0:
        raise Exception('At least one track required')
    
    m3u = [
        '#EXTM3U',
        '#EXTENC:UTF-8',
    ]

    valid_start_path = False

    if start_path != "":
        valid_start_path = os.path.isdir(start_path)

        if valid_start_path is False:
            warn(f'Playlist path not a valid or existing directory: {valid_start_path}')

    if logo != "":
        if os.path.isfile(logo) is False:
            warn(f'Playlist cover not a valid or existing file: {logo}')

        if valid_start_path is True:
            logo = os.path.relpath(logo, start_path)

        m3u.append('#EXTIMG:' + logo)

    if title != "":
        m3u.append('#PLAYLIST:' + title)

    for t in tracklist:
        if os.path.isfile(t) is False:
            warn(f'Not a valid or existing file: {t}')

        if valid_start_path is True:
            t = os.path.relpath(t, start_path)

        m3u.append(f'{t}')

    return '\n'.join(m3u).encode('utf-8')

def save_playlist_to_m3u8(path:str, tracklist:list, logo:str="", title:str="", relative_filepaths:bool=False):
    start_path = ""

    if relative_filepaths is True:
        start_path = os.path.dirname(path)
    
    sbytes = playlist_to_m3u8(tracklist, logo, title, start_path)

    with open(path, 'wb') as f:
        f.write(sbytes)
        f.close()

def download_image(url:str, output_dir:str) -> str:
    fpath = os.path.join(output_dir, os.path.basename(url))

    ext = os.path.splitext(fpath)[1]

    if ext == '':
        fpath += '.jpg'

    r = requests.get(url, stream=True)

    if r.status_code != 200:
        raise RuntimeError('Failed to download image')

    with open(fpath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

        f.close()

    return fpath