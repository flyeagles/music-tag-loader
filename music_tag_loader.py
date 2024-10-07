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
from mutagen.wavpack import WavPack
from mutagen.dsdiff import DSDIFF
from mutagen.dsf import DSF
from mutagen.mp4 import MP4
# import mutagen

logger = logging.getLogger('tag_loader')


def get_mp4_meta(filename):
    audio = MP4(filename)
    logger.debug(audio.tags)
    if audio.tags is None:  # corrupted file. Skip.        
        return None
    return get_mp4_metadata(audio)


def get_mp4_metadata(audio):
    if "\xa9alb" in audio.tags:
        album = audio["\xa9alb"][0]
    else:
        album = ""

    # 'trkn': [(1, 12)]
    if 'trkn' in audio.tags:
        song_index = audio['trkn'][0][0]
    else:
        song_index = "0"

    if "\xa9nam" in audio.tags:
        song_title = audio["\xa9nam"][0]
    else:
        song_title = ""

    if '\xa9ART' in audio.tags:
        song_performer = audio['\xa9ART'][0]
    else:
        song_performer = ""

    if 'aART' in audio.tags:
        album_performer = audio['aART'][0]
    else:
        album_performer = song_performer

    if "\xa9day" in audio.tags:
        year = str(audio["\xa9day"][0])
    else:
        year = ""

    return (album.strip(), album_performer.strip(), year, song_title.strip(), song_performer.strip(), song_index)


def get_wav_meta(filename):
    audio = WAVE(filename)
    logger.debug(audio.tags)
    if audio.tags is None:  # corrupted file. Skip.
        return None
    return get_mp3_id3_metadata(audio)


def get_mp3_meta(filename):
    audio = MP3(filename)
    logger.debug(audio.tags)
    if audio.tags is None:  # corrupted file. Skip.
        return None
    return get_mp3_id3_metadata(audio)


def get_dff_meta(filename):
    audio = DSDIFF(filename)
    logger.debug(audio.tags)
    if audio.tags is None:  # corrupted file. Skip.
        return None
    return get_mp3_id3_metadata(audio)


def get_dsf_meta(filename):
    audio = DSF(filename)
    logger.debug(audio.tags)
    if audio.tags is None:  # corrupted file. Skip.
        return None
    return get_mp3_id3_metadata(audio)


def get_mp3_id3_metadata(audio):
    if "TALB" in audio.tags:
        album = audio["TALB"][0]
    else:
        album = ""

    # 'TRCK': TRCK(encoding=<Encoding.LATIN1: 0>, text=['16/16']
    if 'TRCK' in audio.tags:
        song_index = audio['TRCK'][0].split('/')[0]
    else:
        song_index = "0"

    if 'TIT2' in audio.tags:
        song_title = audio['TIT2'][0]
    else:
        song_title = ""

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
            '''
            Another cue format
            FILE "01 - Call My Name.flac" WAVE
                TITLE "Call My Name"
                TRACK 01 AUDIO
                INDEX 01 00:00:00
            FILE "02 - Crazy Chick.flac" WAVE
                TITLE "Crazy Chick"
                TRACK 02 AUDIO
                INDEX 01 00:00:00 
            '''

            line = "dummy line"
            try:
                song_idx = -1
                song_performer = None
                indexed = False
                for line in IN.readlines():
                    logger.debug(line.strip())
                    match = re.match(r"^REM DATE\s+(.*)", line,
                                     flags=re.IGNORECASE)
                    if match:
                        year = match.group(1)
                        continue

                    match = re.match(r"^PERFORMER\s+(.*)",
                                     line, flags=re.IGNORECASE)
                    if match:
                        performer = match.group(1).replace("\"", "")
                        continue

                    match = re.match(r"^TITLE\s+\"(.*)\"",
                                     line, flags=re.IGNORECASE)
                    if match:
                        album = match.group(1)

                    match = re.match(r"^\s*TRACK\s+(\d+)\s+AUDIO",
                                     line, flags=re.IGNORECASE)
                    if match:
                        indexed = False
                        song_idx = (int)(match.group(1))

                    match = re.match(r"^\s+TITLE\s+\"(.*)\"",
                                     line, flags=re.IGNORECASE)
                    if song_idx >= 0 and match:
                        song_title = match.group(1)

                    match = re.match(r"^\s+PERFORMER\s+(.*)",
                                     line, flags=re.IGNORECASE)
                    if song_idx >= 0 and match:
                        song_performer = match.group(1).replace("\"", "")

                    # a track can have two index lines. so we need skip the second index line.
                    match = re.match(
                        r"^\s+INDEX\s+\d+\s+(\d+):(\d+):(\d+)", line, flags=re.IGNORECASE)
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
                logger.error(e)
                logger.error(line)
                err_str_list.append(str(e))

    logger.debug(song_list)
    if len(album) == 0:
        logger.error("Cannot find album name!")
        logger.error(os.path.join(os.getcwd(), filename))
        logger.error((album, performer, year))
        logger.error("\n".join(err_str_list))
        exit(1)

    return (album.strip(), performer.strip(), year.strip(), song_list)


music_func_map = {"flac": get_flac_meta,
                  'ape': get_ape_meta,
                  'mp3': get_mp3_meta,
                  'wav': get_wav_meta,
                  'dff': get_dff_meta,
                  'dsf': get_dsf_meta,
                  'mp4': get_mp4_meta,
                  'm4a': get_mp4_meta,
                  'cue': parse_cue
                  }


def handle_music_file(filename, root, music, max_seq, albums):
    fullpath = os.path.join(root, filename)
    logger.debug(f'{music}: {fullpath}')
    result_tuple = (music_func_map[music])(filename)
    return result_tuple


def get_file_surfix(filename):
    return filename.split('.')[-1].lower()


def get_albums(baseroot, max_seq, albums, recrawl_songs):
    print(baseroot)

    new_album_list = []
    new_song_list = []
    for (root, dirs, files) in os.walk(baseroot, topdown=True):
        # print(root) full path to a folder
        # print(dirs) subfolders within root
        # print(files) files within root
        os.chdir(root)
        logger.debug(root)
        # root is the path to the album
        no_cue = True
        result_tuple = None
        album, album_performer, year = "", "", ""
        song_list = []
        cue_count = 0
        for filename in files:
            logger.info(filename)
            surfix = get_file_surfix(filename)
            if surfix == 'cue':
                result_tuple = handle_music_file(
                    filename, root, 'cue', max_seq, albums)
                if result_tuple is not None:
                    # here I want to continue the check to see if there is another CUE file in the same folder.
                    cue_count += 1

        if cue_count > 1:
            logger.error(
                f"More than one cue file found in {root}. =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=!!!!!!")

        if result_tuple is None:
            for filename in files:
                try:
                    surfix = get_file_surfix(filename)
                    if surfix in ['flac', 'ape', 'mp3', 'wav', 'dff', 'dsf', 'mp4', 'm4a']:
                        result_tuple = handle_music_file(
                            filename, root, surfix, max_seq, albums)
                        if result_tuple is None:
                            continue

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
                new_album_list.append(
                    [album, album_performer, year, max_seq, album_performer, root])

                # song list is [(song_index, song_title, song_performer), ... )]
                # need add the album's seq number to the end of tuples.
                track_ids = []
                for idx, song in enumerate(song_list):
                    if song[-1] in track_ids:
                        logger.error(
                            f"-----------------> {song[-1]} in {max_seq} is duplicated!")
                    track_ids.append(song[-1])
                    song_list[idx] = song + (max_seq,)
                new_song_list.extend(song_list)
            else:
                # print duplicate album info
                logger.info("======================================")
                logger.info(pprint.pformat(existing_album))
                if recrawl_songs:
                    song_seq = existing_album['seq']
                    track_ids = []
                    for idx, song in enumerate(song_list):
                        if song[-1] in track_ids:
                            logger.error(
                                f"-----------------> {song[-1]} in {song_seq} is duplicated!")
                        track_ids.append(song[-1])
                        song_list[idx] = song + (song_seq,)
                    new_song_list.extend(song_list)
                else:
                    # the album is already in the albums dataframe, skip the song handling
                    pass

    sorted_album_list = sorted(new_album_list)
    logger.info(pprint.pformat(sorted_album_list))
    l_total = len(sorted_album_list)
    for idx in range(l_total - 1):
        # [album, album_performer, year, max_seq])
        if sorted_album_list[idx][0] == sorted_album_list[idx+1][0] and sorted_album_list[idx][1] == sorted_album_list[idx+1][1]:
            logger.error(
                f"============== Duplicated album {sorted_album_list[idx][0]} {sorted_album_list[idx][1]} {sorted_album_list[idx+1][-1]} {sorted_album_list[idx][-1]}")
    # pprint.pprint(sorted(new_song_list, key=lambda x: (x[3], x[2])))

    # add new album to albums dataframe
    new_albums = pd.DataFrame(new_album_list, columns=[
                              'title', 'performer', 'release_date', 'seq', 'performer_zh', 'path'])
    # add new songs to songs dataframe
    new_songs = pd.DataFrame(new_song_list, columns=[
        'title', 'performer', 'seq', 'albumid'])

    print(new_albums)
    print(new_songs)
    return new_albums, new_songs, max_seq


'''
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
                        "INSERT INTO albums(title, performer, release_date, performer_zh) VALUES (?,?,?,?) ON CONFLICT DO NOTHING", [item])
                except sqlite3.InterfaceError as e:
                    logger.error(f"Type par0: {type(item[0])}")
                    logger.error(f"Type par1: {type(item[1])}")
                    logger.error(f"Type par2: {type(item[2])}")
                    logger.error(item)
                    logger.error(e)
                    exit(1)
        else:
            cursor.executemany(
                "INSERT INTO albums(title, performer, release_date, performer_zh) VALUES (?, ?,?,?) ON CONFLICT DO NOTHING", albums)

        CONN.commit()
        cursor.close()
'''


def load_albums_to_dataframe(sqlitefile):
    # load albums from sqlite3 db file into pandas dataframe
    with sqlite3.connect(sqlitefile) as CONN:
        albums = pd.read_sql_query("select * from albums", CONN)
        print(albums)
        return albums


def set_logger(args, logfile):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.info:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if logfile is not None:
        file_handler = logging.FileHandler(logfile)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", type=str, default='.',
                        help="folder to scan recursively, separted with ;")
    parser.add_argument("-s", "--sqlite", type=str, required=True,
                        help="path to sqlite3 db file")
    parser.add_argument("--song", default=False, action='store_true',
                        help="whether to recrawl songs for existing albums")
    parser.add_argument("--debug", default=False, action='store_true',
                        help="whether to enable debug")
    parser.add_argument("--info", default=False, action='store_true',
                        help="whether to enable info logging. info is a higher level than debug.")
    parser.add_argument("--logfile", default=False, action='store_true',
                        help="whether to write log to a file.")
    args = parser.parse_args()

    if args.logfile:
        base_dir = os.path.dirname(os.path.realpath(__file__))
        set_logger(args, os.path.join(base_dir, 'tag_loader.log'))
    else:
        set_logger(args, None)

    albums = load_albums_to_dataframe(args.sqlite)
    # get the max value of seq in albums
    max_seq = albums['seq'].max()
    # set max_seq to 0 if it is nan
    if pd.isna(max_seq):
        max_seq = 0
    print(f'max seq: {max_seq}')

    dirs = args.dir.split(';')
    new_album_count = 0
    new_song_count = 0
    for dir in dirs:
        if dir == '':
            continue
        albums, new_songs, max_seq = get_albums(
            dir, max_seq, albums, args.song)
        # write albums dataframe and new_songs dataframe back to sqlite3 database
        print(albums)
        albums.to_sql('albums', sqlite3.connect(
            args.sqlite), if_exists='append', index=False)
        new_songs.to_sql('songs', sqlite3.connect(
            args.sqlite), if_exists='append', index=False)

        new_album_count += len(albums)
        new_song_count += len(new_songs)

    print(
        f'Found {new_album_count} albums and {new_song_count} songs.')

    exit(0)

    write_albums(args.sqlite, albums, args.debug)
