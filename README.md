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

