import argparse
import logging
import re
import os

logger = logging.getLogger('replace_cue_titles')


def parse_cue(filename,inputfile):
    encodings = ['utf8', 'gbk', 'big5']
    err_str_list = []
    title_list = []
    singer_list = []
    for encoding in encodings:
        with open(inputfile, 'r', encoding=encoding) as IN_TITLES:
            try:
                for line in IN_TITLES.readlines():
                    if '|' not in line:
                        title_list.append(line.strip())
                    else:
                        # 梭罗河之恋/美黛
                        fields = line.split('|')
                        title_list.append(fields[0].strip())
                        singer_list.append(fields[1].strip())

                break
            except UnicodeDecodeError as e:
                # need change to GBK encoding.
                # fallback to second encoding value.
                logger.debug(e)

    if len(title_list) == 0:
        logger.debug("Title list is empty. Exit now!")
        exit(1)
    
    logger.info(str(title_list), str(singer_list))
    
    outputfile = filename+'.new.txt'
    succeed = False
    for encoding in encodings:
        with open(filename, 'r', encoding=encoding) as IN, open(outputfile,'w',encoding='utf8') as OUT:            
            try:
                '''
                Sample:
                FILE "高胜美 - 美不胜收经典金选.wav" WAVE
                  TRACK 01 AUDIO
                    TITLE "音轨01"
                    PERFORMER "高胜美"
                    FLAGS DCP
                    INDEX 01 00:00:00
                  TRACK 02 AUDIO
                    TITLE "音轨02"
                    FLAGS DCP
                    INDEX 01 04:42:02
                '''
                in_track = False
                for line in IN.readlines():
                    match = re.match(r"^\s*TRACK\s+\d+\s+AUDIO", line, flags=re.IGNORECASE)
                    if match:
                        in_track = True
                        OUT.write(line)
                        logger.info("---" + line)
                        continue
                        
                    if in_track:
                        match = re.match(r"^(\s*TITLE)\s+", line, flags=re.IGNORECASE)
                        if match:
                            # need replace the title now.
                            OUT.write(match.group(1) + ' "' + title_list[0] +'"\n')
                            logger.info(title_list[0])
                            title_list.pop(0)
                            continue
                        
                        match2 = re.match(r"^(\s*PERFORMER)\s+", line, flags=re.IGNORECASE)
                        if match2:
                            if len(singer_list) > 0:
                                # replace performaner if the singer_list is not empty
                                OUT.write(match2.group(1) + ' "' + singer_list[0] +'"\n')
                                logger.info(singer_list[0])
                                singer_list.pop(0)
                                continue
                                
                        match_index = re.match(r"^(\s*INDEX)\s+", line, flags=re.IGNORECASE)
                        if match_index:
                            in_track = False


                    OUT.write(line)
                    logger.info(line)

                # all lines parsed. break out of loop for encoding types
                # swap old file and new file
                succeed = True
                break

            except UnicodeDecodeError as e:
                # need change to GBK encoding.
                # fallback to second encoding value.
                logger.debug(f"Current encoding is {encoding}")
                logger.debug(e)
                
    if succeed:
        os.rename(filename, filename+'.old')
        os.rename(outputfile, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--cue", type=str, required=True,
                        help="cue file to process")
    parser.add_argument("-i", "--titles", type=str, required=True,
                        help="title file for input")
    parser.add_argument("--debug", default=False, action='store_true',
                        help="whether to enable debug")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.ERROR)

    print(args)
    parse_cue(args.cue, args.titles)
