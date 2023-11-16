# music-tag-loader

This is a Python program to scan and parse music file tags, and generate SQL commands to store the data in database.

## Scan

### CUE
It will scan CUE files first, and parse CUE file structure to retrive following album information:
- REM DATE 
- PERFORMER
- TITLE

### Embedded Tags in music files
If there is no CUE file in a folder, it will read music file directly and get ALBUM, PERFORMER and TITLE data directly.
It can read ape, mp3, flac, and wav files.

## Song Data

I want to get individual song's information.
- Title
- PERFORMER (if existing in the track info)
- Length in seconds

# Music Tag Batch Insert

I can get the song's title and performers through introduction text, but I don't want to copy/paste those text into individual song's tag fields through foobar2000 GUI operation. I want to run a script to get the text from input file, split it into the right field values, and then embed those values into each song file's metadata.

## Tag processing
I am using mutagend module to do the tag processing. https://mutagen.readthedocs.io/en/latest/
It supports ASF, FLAC, MP4, Monkey’s Audio, MP3, Musepack, Ogg Opus, Ogg FLAC, Ogg Speex, Ogg Theora, Ogg Vorbis, True Audio, WavPack, OptimFROG, and AIFF audio files. All versions of ID3v2 are supported, and all standard ID3v2.4 frames are parsed. Mutagen works with Python 3.8+ (CPython and PyPy) on Linux, Windows and macOS, and has no dependencies outside the Python standard library. 

v1.47.0 is used for now.