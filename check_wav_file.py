#!/usr/bin/env python

import sys

from mutagen._riff import RiffFile


def validate_chunk(chunk, level=0):
    valid = True
    indent = "  " * level
    if hasattr(chunk, 'subchunks'):
        print("{0}{1} {2}\t(offset: {3}, size: {4}, data-size: {5})".format(
            indent, chunk.id, chunk.name, chunk.offset, chunk.size,
            chunk.data_size))
        subchunk_size = 12
        for subchunk in chunk.subchunks():
            subchunk_size += subchunk.size
            valid &= validate_chunk(subchunk, level + 1)
        sizes_match = subchunk_size == chunk.size
        valid &= sizes_match
        print("{0}Total: {1} bytes{2}".format(indent, subchunk_size,
            "" if sizes_match else " !SIZE MISMATCH!"))
    else:
        print("{0}{1}\t(offset: {2}, size: {3}, data-size: {4})".format(
            indent, chunk.id, chunk.offset, chunk.size, chunk.data_size))
    return valid


def main():
    f = open(sys.argv[1], 'rb')
    riff = RiffFile(f)
    valid = validate_chunk(riff.root)

    f.seek(0, 2)
    size = f.tell()
    sizes_match = size == riff.root.size
    valid &= sizes_match
    print("\nFile size: {0} bytes{1}".format(
        size, "" if sizes_match else " !SIZE MISMATCH!"))

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
   