import argparse
import os
import re


def append_timestamp(filename: str, length: int):
    with open(filename, 'r') as IN:
        lines = [1 for line in IN]
        linecount = len(lines)
        avg_interval = length/(linecount+2)

    newfilename = 'new_'+filename
    with open(filename, 'r') as IN:
        with open(newfilename, 'w') as OUT:
            timing = 0
            for line in IN:
                line = re.sub(r'\[.*?\]', '', line)
                line = line.strip()
                minutes = int(timing / 60)
                seconds = int(timing % 60)
                newline = f'[{minutes:02d}:{seconds:02d}.00]{line}'
                timing += avg_interval
                OUT.writelines(newline+'\n')

    os.rename(filename, filename+'.bak')
    os.rename(newfilename, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--file", type=str, required=True,
                        help="lrc file name to append timestamp")
    parser.add_argument("-t", "--time", type=int, required=False,
                        default=240,
                        help="total length of the song in seconds. Default to 240.")
    args = parser.parse_args()
    append_timestamp(args.file, args.time)
