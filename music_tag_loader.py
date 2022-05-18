import argparse
from email.mime import base
import os
import re
import logging

from mutagen.flac import FLAC
from mutagen.apev2 import APEv2File
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
import mutagen
from mutagen.wavpack import WavPack

logger = logging.getLogger('tag_loader')

def get_wav_meta(filename):
    audio = WAVE(filename)
    print(audio.pprint())
    print(audio.tags)
    return get_mp3_metadata(audio)

def get_flac_meta(filename):
    audio = FLAC(filename)
    return get_metadata(audio)

def get_mp3_meta(filename):
    audio = MP3(filename)
    return get_mp3_metadata(audio)

def get_mp3_metadata(audio):    
    album = audio["TALB"][0]
    if 'TPE1' in audio.tags:
        performer = audio['TPE1'][0]
    else:
        performer = audio['TPE2'][0]
    
    if "TDRC" in audio.tags:
        year = str(audio["TDRC"][0])
    else:
        year = ""

    return (album, performer, year)


def get_ape_meta(filename):
    audio = APEv2File(filename)
    return get_metadata(audio)

def get_metadata(audio):    
    album = audio["ALBUM"][0]
    if 'ALBUMARTIST' in audio.tags:
        performer = audio['ALBUMARTIST'][0]
    elif 'ARTIST' in audio.tags:
        performer = audio['ARTIST'][0]
    else:
        performer = audio['ALBUM ARTIST'][0]

    if "DATE" in audio.tags:
        year = audio["DATE"][0]
    elif 'YEAR' in audio.tags:
        year = audio["YEAR"][0]
    else:
        year = ""

    return (album, performer, year)

def parse_cue(filename):
    album = ""
    performer = ""
    year = ""
    encodings = ['utf8', 'gbk', 'big5']
    for encoding in encodings:
        with open(filename, 'r', encoding=encoding) as IN:
            try:
                for line in IN.readlines():
                    match = re.match("^REM DATE\s+(.*)", line, flags=re.IGNORECASE)
                    if match:
                        year = match.group(1)
                        continue

                    match = re.match("^PERFORMER\s+(.*)", line, flags=re.IGNORECASE)
                    if match:
                        performer = match.group(1).replace("\"", "")
                        continue

                    match = re.match("^TITLE\s+\"(.*)\"", line, flags=re.IGNORECASE)
                    if match:
                        album = match.group(1)

                # all lines parsed. break out of loop
                break

            except UnicodeDecodeError as e:
                # need change to GBK encoding.
                # fallback to second encoding value.
                logger.debug(e)

    if len(album) == 0:
        logger.error(os.path.join(os.getcwd(), filename))
        logger.error((album, performer, year))
        exit(1)

    return (album, performer, year)

def get_albums(baseroot):
    print(baseroot)

    albums = []
    for (root,dirs,files) in os.walk(baseroot, topdown=True):
        # print(root) full path to a folder
        # print(dirs) subfolders within root
        # print(files) files within root
        os.chdir(root)
        no_cue = True
        for filename in files:
            fullpath = os.path.join(root, filename)
            if filename.endswith("cue") or filename.endswith("CUE"):
                logger.debug(fullpath)
                albums.append(parse_cue(filename))
                no_cue = False
                break

        if no_cue:
            for filename in files:
                fullpath = os.path.join(root, filename)
                if filename.endswith('flac') or filename.endswith('FLAC'):
                    logger.debug('flac: ' + fullpath)
                    albums.append(get_flac_meta(filename))
                    no_cue = False
                    break

                if filename.endswith('ape') or filename.endswith('APE'):
                    logger.debug('ape: '+fullpath)
                    albums.append(get_ape_meta(filename))
                    no_cue = False
                    break

                if filename.endswith('mp3') or filename.endswith('MP3'):
                    logger.debug('mp3: '+fullpath)
                    albums.append(get_mp3_meta(filename))
                    no_cue = False
                    break

                if filename.endswith('wav') or filename.endswith('WAV'):
                    logger.debug('wav: '+fullpath)
                    albums.append(get_wav_meta(filename))
                    no_cue = False
                    break

        if no_cue and len(files) > 1:
            logger.error(f"No cue in {root}.")
            logger.error(files)
    return albums

import sqlite3


def write_albums(sqlitefile, albums, debug):
    print(sqlitefile)
    with sqlite3.connect(sqlitefile) as CONN:
        cursor = CONN.cursor()
        for row in cursor.execute('select count(*) from albums'):
            print(f'{row[0]} records exists.')

        # insert multiple records using the more secure "?" method
        # albums = [('title', 'performer', 'year'),('title', 'performer', 'year')]
        if debug:
            for item in albums:
                try:
                    cursor.executemany("INSERT INTO albums VALUES (?,?,?) ON CONFLICT DO NOTHING", [item])
                except sqlite3.InterfaceError as e:
                    logger.error(f"Type par0: {type(item[0])}")
                    logger.error(f"Type par1: {type(item[1])}")
                    logger.error(f"Type par2: {type(item[2])}")
                    logger.error(item)
                    logger.error(e)
                    exit(1)
        else:
            cursor.executemany("INSERT INTO albums VALUES (?,?,?) ON CONFLICT DO NOTHING", albums)

        CONN.commit()            
        cursor.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", type=str, default = '.',
                        help="folder to scan recursively")
    parser.add_argument("-s", "--sqlite", type=str, required=True,
                        help="path to sqlite3 db file")
    parser.add_argument("--debug", default=False, action='store_true',
                        help="whether to enable debug")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    albums = get_albums(args.dir)
    
    print(f'Found {len(albums)} albums.')

    write_albums(args.sqlite, albums, args.debug)
