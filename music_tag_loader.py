import argparse
from email.mime import base
import os
import re
import logging

logger = logging.getLogger('tag_loader')

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
        for filename in files:
            if filename.endswith("cue") or filename.endswith("CUE"):
                logger.debug(filename)
                albums.append(parse_cue(filename))
                break
    return albums

import sqlite3


def write_albums(sqlitefile, albums):
    print(sqlitefile)
    with sqlite3.connect(sqlitefile) as CONN:
        cursor = CONN.cursor()
        for row in cursor.execute('select count(*) from albums'):
            print(f'{row[0]} records exists.')

        # insert multiple records using the more secure "?" method
        # albums = [('title', 'performer', 'year'),('title', 'performer', 'year')]
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

    write_albums(args.sqlite, albums)
