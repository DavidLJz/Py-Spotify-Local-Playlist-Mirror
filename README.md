Recreates a Spotify playlist using local tracks.

Compares each track's metadata in a Spotify playlist to local music file's metadata to recreate the playlist.

If files cannot be found that match a song it will be skipped. The output is saved as M3U File.

Metadata for (lowercase) comparison:
- Album
- Artist
- Track name

Make sure to use the same track, album and artist names as Spotify in your audio files so the script can find them.

```
usage: mirror_playlist.py [-h] [-o OUTPUT] [-t TITLE] [-c COVER] playlist_id source_dir

Mirror a Spotify playlist to a m3u8 playlist file with local tracks

positional arguments:
  playlist_id           Spotify Playlist ID to mirror
  source_dir            The source directory to search for tracks (including subdirectories)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        The full output file path, if not given will save to current directory as
                        $playlist_id.m3u8. Cover image will be downloaded to the same directory.
  -t TITLE, --title TITLE
                        The title of the playlist, if not given will use the Spotify given name
  -c COVER, --cover COVER
                        The cover image of the playlist, if not given will download and use the Spotify
                        cover
```