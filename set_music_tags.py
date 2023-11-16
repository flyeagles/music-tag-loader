import sqlite3
import argparse
import os
import re
import logging

from mutagen.flac import FLAC
from mutagen.apev2 import APEv2File
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.id3 import ID3, TIT2, TALB, TRCK, TPE1, TDRC
from mutagen.easyid3 import EasyID3


# import mutagen

logger = logging.getLogger('tag_loader')


def set_wav_meta(filename, album, year, total, title_info, track_num):
    audio = WAVE(filename)
    audio.pprint()
    logger.debug(audio.tags)
    set_mp3_metadata(audio, album, year, total, title_info, track_num)


def set_flac_meta(filename, album, year, total, title_info):
    audio = FLAC(filename)
    logger.debug(audio.tags)
    set_metadata(audio, album, year, total, title_info)


def set_mp3_meta(filename, album, year, total, title_info):
    audio = MP3(filename)
    logger.debug(audio.tags)
    set_mp3_metadata(audio, album, year, total, title_info)


def set_mp3_metadata(audio, album, year, total, title_info, track_num):
    '''
    {'TIT2': TIT2(encoding=<Encoding.UTF16: 1>, text=['2']),  # track title
    'TALB': TALB(encoding=<Encoding.UTF16: 1>, text=['3']),     # album title
    'TRCK': TRCK(encoding=<Encoding.LATIN1: 0>, text=['5']),    # track number
    'TPE1': TPE1(encoding=<Encoding.UTF16: 1>, text=['1'])}   #artist name
    '''
    audio['TIT2'] = TIT2(encoding=3, text=[title_info[0]])
    audio['TPE1'] = TPE1(encoding=3, text=[title_info[1]])
    audio['TRCK'] = TRCK(encoding=3, text=[f'{track_num}/{total}'])
    audio['TALB'] = TALB(encoding=3, text=[album])
    audio['TDRC'] = TDRC(encoding=3, text=[year])

    audio.save()


def set_ape_meta(filename, title_info):
    audio = APEv2File(filename)
    logger.debug(audio.tags)
    set_metadata(audio, title_info)


def set_metadata(audio):
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
    err_str_list = []
    for encoding in encodings:
        with open(filename, 'r', encoding=encoding) as IN:
            try:
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

                # all lines parsed. break out of loop
                break

            except UnicodeDecodeError as e:
                # need change to GBK encoding.
                # fallback to second encoding value.
                logger.debug(e)
                err_str_list.append(str(e))

    if len(album) == 0:
        logger.error(os.path.join(os.getcwd(), filename))
        logger.error((album, performer, year))
        logger.error("\n".join(err_str_list))
        exit(1)

    return (album, performer, year)


music_func_map = {"flac": set_flac_meta,
                  'ape': set_ape_meta,
                  'mp3': set_mp3_meta,
                  'wav': set_wav_meta,
                  'cue': parse_cue
                  }


def handle_music_file(filename, album, year, total, title_info, track_num):
    print(filename)
    surfix = filename.split('.')[-1].lower()
    (music_func_map[surfix])(filename, album,
                             year, total, title_info, track_num)


def is_music_file(filename):
    norm_filename = filename.lower()
    return norm_filename.endswith('flac') or norm_filename.endswith('ape') or norm_filename.endswith('mp3') or norm_filename.endswith('wav')


def set_tags(baseroot, album, year, total, song_title_list):
    print(baseroot)

    oldpath = os.getcwd()
    os.chdir(baseroot)

    music_file_list = [file for file in os.listdir(".") if is_music_file(file)]
    sorted_music_file_list = sorted(music_file_list)

    for idx, filename in enumerate(sorted_music_file_list):
        handle_music_file(filename, album, year, total,
                          song_title_list[idx], idx+1)

    os.chdir(oldpath)
    return idx+1


def parse_song_file(filename):
    '''
    ALBUM|成都
    DATE|2017
    TOTAL|13
    成都|赵雷
    理想|赵雷
    '''
    song_title_list = []
    with open(filename, 'r', encoding="utf8") as IN:
        for line in IN.readlines():
            line = line.strip()
            if len(line) == 0:
                continue
            song_title_list.append(line.split('|'))
    return (song_title_list[0][1], song_title_list[1][1], song_title_list[2][1], song_title_list[3:])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", type=str, default='.',
                        help="folder containing the music files to set tags.")
    parser.add_argument("-f", "--file", type=str, required=True,
                        help="path to title and performer file. The file is CSV file with | as separator.")
    parser.add_argument("--debug", default=False, action='store_true',
                        help="whether to enable debug")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    album, year, total, song_title_list = parse_song_file(args.file)
    print(album, year, total, song_title_list)

    count = set_tags(args.dir, album, year, total, song_title_list)

    print(f'Processed {count} songs.')
