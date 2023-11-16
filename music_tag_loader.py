import sqlite3
import argparse
import os
import re
import logging
import pandas as pd
import pprint

from mutagen.flac import FLAC
from mutagen.apev2 import APEv2File
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
# import mutagen

logger = logging.getLogger('tag_loader')


def get_wav_meta(filename):
    audio = WAVE(filename)
    logger.debug(audio.tags)
    return get_mp3_metadata(audio)


def get_mp3_meta(filename):
    audio = MP3(filename)
    logger.debug(audio.tags)
    return get_mp3_metadata(audio)


def get_mp3_metadata(audio):
    album = audio["TALB"][0]

    # 'TRCK': TRCK(encoding=<Encoding.LATIN1: 0>, text=['16/16']
    song_index = audio['TRCK'][0].split('/')[0]
    song_title = audio['TIT2'][0]
    if 'TPE1' in audio.tags:
        song_performer = audio['TPE1'][0]
    else:
        song_performer = ""

    if 'TPE2' in audio.tags:
        album_performer = audio['TPE2'][0]
    else:
        album_performer = song_performer

    if "TDRC" in audio.tags:
        year = str(audio["TDRC"][0])
    else:
        year = ""

    return (album.strip(), album_performer.strip(), year, song_title.strip(), song_performer.strip(), song_index)


def get_flac_meta(filename):
    audio = FLAC(filename)
    logger.debug(audio.tags)
    return get_metadata(audio)


def get_ape_meta(filename):
    audio = APEv2File(filename)
    logger.debug(audio.tags)
    return get_metadata(audio)


def get_metadata(audio):
    album = audio["ALBUM"][0]
    if 'ARTIST' in audio.tags:
        song_performer = audio['ARTIST'][0]
    else:
        song_performer = ""

    if 'ALBUMARTIST' in audio.tags:
        album_performer = audio['ALBUMARTIST'][0]
    elif 'ALBUM ARTIST' in audio.tags:
        album_performer = audio['ALBUM ARTIST'][0]
    else:
        album_performer = ""

    if album_performer == "":
        album_performer = song_performer

    if "DATE" in audio.tags:
        year = audio["DATE"][0]
    elif 'YEAR' in audio.tags:
        year = audio["YEAR"][0]
    else:
        year = ""

    if 'TRACKNUMBER' in audio.tags:
        song_index = audio['TRACKNUMBER'][0]
    else:
        song_index = ""

    if 'TITLE' in audio.tags:
        song_title = audio['TITLE'][0]
    else:
        song_title = ""

    return (album.strip(), album_performer.strip(), year, song_title.strip(), song_performer.strip(), song_index)


def parse_cue(filename):
    album = ""
    performer = ""
    year = ""
    encodings = ['utf8', 'gbk', 'big5']
    err_str_list = []
    song_list = []
    for encoding in encodings:
        with open(filename, 'r', encoding=encoding) as IN:
            '''
            REM DATE 1987
            PERFORMER "Erich Kunzel, CINCINNATI POPS ORCHESTRA"
            TITLE "Pomp & Pizazz"
            FILE "Erich Kunzel, CINCINNATI POPS ORCHESTRA - Pomp & Pizazz.wav" WAVE
              TRACK 01 AUDIO
                TITLE "Olympic Fanfare"
                PERFORMER "Williams, John"
                INDEX 01 00:00:00
              TRACK 02 AUDIO
                TITLE "Towards a New Life, Op.35c"
                PERFORMER "Suk, Josef"
                INDEX 00 04:21:00
                INDEX 01 04:22:32
            '''
            try:
                song_idx = -1
                song_performer = None
                indexed = False
                for line in IN.readlines():
                    match = re.match("^REM DATE\s+(.*)", line,
                                     flags=re.IGNORECASE)
                    if match:
                        year = match.group(1)
                        continue

                    match = re.match("^PERFORMER\s+(.*)",
                                     line, flags=re.IGNORECASE)
                    if match:
                        performer = match.group(1).replace("\"", "")
                        continue

                    match = re.match("^TITLE\s+\"(.*)\"",
                                     line, flags=re.IGNORECASE)
                    if match:
                        album = match.group(1)

                    match = re.match("^\s*TRACK\s+(\d+)\s+AUDIO",
                                     line, flags=re.IGNORECASE)
                    if match:
                        indexed = False
                        song_idx = (int)(match.group(1))

                    match = re.match("^\s+TITLE\s+\"(.*)\"",
                                     line, flags=re.IGNORECASE)
                    if song_idx >= 0 and match:
                        song_title = match.group(1)

                    match = re.match("^\s+PERFORMER\s+(.*)",
                                     line, flags=re.IGNORECASE)
                    if song_idx >= 0 and match:
                        song_performer = match.group(1).replace("\"", "")

                    # a track can have two index lines. so we need skip the second index line.
                    match = re.match(
                        "^\s+INDEX\s+\d+\s+(\d+):(\d+):(\d+)", line, flags=re.IGNORECASE)
                    if match and not indexed:  # we are done with current song.
                        indexed = True
                        if song_performer is None:
                            song_performer = performer
                        song_list.append(
                            (song_title.strip(), song_performer.strip(), song_idx))
                        song_performer = None

                # all lines parsed. break out of loop
                break

            except UnicodeDecodeError as e:
                # need change to GBK encoding.
                # fallback to second encoding value.
                logger.debug(e)
                err_str_list.append(str(e))

    print(song_list)
    if len(album) == 0:
        logger.error(os.path.join(os.getcwd(), filename))
        logger.error((album, performer, year))
        logger.error("\n".join(err_str_list))
        exit(1)

    return (album.strip(), performer.strip(), year.strip(), song_list)


music_func_map = {"flac": get_flac_meta,
                  'ape': get_ape_meta,
                  'mp3': get_mp3_meta,
                  'wav': get_wav_meta,
                  'cue': parse_cue
                  }


def handle_music_file(filename, root, music, max_seq, albums):
    fullpath = os.path.join(root, filename)
    logger.debug(f'{music}: {fullpath}')
    result_tuple = (music_func_map[music])(filename)
    return result_tuple


def get_file_surfix(filename):
    return filename.split('.')[-1].lower()


def get_albums(baseroot, max_seq, albums):
    print(baseroot)

    new_album_list = []
    new_song_list = []
    for (root, dirs, files) in os.walk(baseroot, topdown=True):
        # print(root) full path to a folder
        # print(dirs) subfolders within root
        # print(files) files within root
        os.chdir(root)
        print(root)
        no_cue = True
        result_tuple = None
        album, album_performer, year = "", "", ""
        song_list = []
        for filename in files:
            print(filename)
            surfix = get_file_surfix(filename)
            if surfix == 'cue':
                result_tuple = handle_music_file(
                    filename, root, 'cue', max_seq, albums)
            if result_tuple is not None:
                break

        if result_tuple is None:
            for filename in files:
                try:
                    surfix = get_file_surfix(filename)
                    if surfix in ['flac', 'ape', 'mp3', 'wav']:
                        result_tuple = handle_music_file(
                            filename, root, surfix, max_seq, albums)
                        (album, album_performer, year,
                         song_title, song_performer, song_index) = result_tuple
                        song_list.append(
                            (song_title, song_performer, song_index))
                except KeyError as e:
                    logger.error(e)
                    logger.error(f'{root}//{filename}')
                    exit(1)
        else:
            (album, album_performer, year, song_list) = result_tuple

        if len(album) == 0 and len(files) > 1:
            logger.error(f"No music file found in {root}.")
            logger.error(files)
        elif len(album) > 0:
            # we find album info.
            # Need check if album exists in albums dataframe.
            # both album title and performaer must match.
            # if not, add new album to albums dataframe

            existing_album = albums.loc[(albums['title'] == album) & (
                albums["performer"] == album_performer)]
            if len(existing_album) == 0:
                max_seq += 1
                # dataframe row is [title, performer, release_date, seq]
                # add new row to dataframe albums
                # dataframe has no append() method.
                new_album_list.append([album, album_performer, year, max_seq])

                # song list is [(song_index, song_title, song_performer), ... )]
                # need add the album's seq number to the end of tuples.
                for idx, song in enumerate(song_list):
                    song_list[idx] = song + (max_seq,)
                new_song_list.extend(song_list)

            else:
                # the album is already in the albums dataframe, skip the song handling
                pass

    pprint.pprint(new_album_list)
    pprint.pprint(new_song_list)

    # add new album to albums dataframe
    new_albums = pd.DataFrame(new_album_list, columns=[
                              'title', 'performer', 'release_date', 'seq'])
    # add new songs to songs dataframe
    new_songs = pd.DataFrame(new_song_list, columns=[
        'title', 'performer', 'seq', 'albumid'])

    print(new_albums)
    print(new_songs)
    return new_albums, new_songs


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
                    cursor.executemany(
                        "INSERT INTO albums VALUES (?,?,?) ON CONFLICT DO NOTHING", [item])
                except sqlite3.InterfaceError as e:
                    logger.error(f"Type par0: {type(item[0])}")
                    logger.error(f"Type par1: {type(item[1])}")
                    logger.error(f"Type par2: {type(item[2])}")
                    logger.error(item)
                    logger.error(e)
                    exit(1)
        else:
            cursor.executemany(
                "INSERT INTO albums VALUES (?,?,?) ON CONFLICT DO NOTHING", albums)

        CONN.commit()
        cursor.close()


def load_albums_to_dataframe(sqlitefile):
    # load albums from sqlite3 db file into pandas dataframe
    with sqlite3.connect(sqlitefile) as CONN:
        albums = pd.read_sql_query("select * from albums", CONN)
        print(albums)
        return albums


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", type=str, default='.',
                        help="folder to scan recursively, separted with ;")
    parser.add_argument("-s", "--sqlite", type=str, required=True,
                        help="path to sqlite3 db file")
    parser.add_argument("--debug", default=False, action='store_true',
                        help="whether to enable debug")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    albums = load_albums_to_dataframe(args.sqlite)
    # get the max value of seq in albums
    max_seq = albums['seq'].max()
    # set max_seq to 0 if it is nan
    if pd.isna(max_seq):
        max_seq = 0
    print(f'max seq: {max_seq}')

    dirs = args.dir.split(';')
    for dir in dirs:
        if dir == '':
            continue
        albums, new_songs = get_albums(dir, max_seq, albums)
        # write albums dataframe and new_songs dataframe back to sqlite3 database
        print(albums)
        albums.to_sql('albums', sqlite3.connect(
            args.sqlite), if_exists='append', index=False)
        new_songs.to_sql('songs', sqlite3.connect(
            args.sqlite), if_exists='append', index=False)

    print(f'Found {len(albums)} albums.')

    exit(0)

    write_albums(args.sqlite, albums, args.debug)
