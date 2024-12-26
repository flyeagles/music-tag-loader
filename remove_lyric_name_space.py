import os
import argparse

def walk(target:str, act:bool) -> int:
    cwd = os.getcwd()
    os.chdir(target)
    changed = 0
    for root, dirs, files in os.walk('.'):
        tmpcwd = os.getcwd()
        os.chdir(root)
        for file in files:
            if file.endswith('.lrc') and ' - ' in file:
                newname = file.replace(' - ', '-')
                print(f'{file} --> {newname}')
                changed += 1
                if act:
                    os.rename(file, newname)

        os.chdir(tmpcwd)

    os.chdir(cwd)
    return changed

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", type=str, default='.',
                        help="folder to scan recursively, separted with ;")
    parser.add_argument("--act", action='store_true', default=False,
                        help="whether to actually change file names")
    args = parser.parse_args()
    print(args)
    changed = walk(args.dir, args.act)
    if args.act:
        print(f'Changed {changed} file names.')
    else:
        print(f'{changed} file names need be changed.')

if __name__ == '__main__':
    main()
