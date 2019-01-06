#!/usr/bin/env python3
#
# Author: Vikas Chouhan (presentisgood@gmail.com).

import os
import sys
import argparse
import pandas as pd
import subprocess


def rp(x):
    return os.path.expanduser(x)
# enddef

def mkdir(x):
    if not os.path.isdir(x):
        os.mkdir(x)
    # endif
# enddef

def chkfile(x):
    if not os.path.isfile(x):
        print('{} doesnot exist !!'.format(x))
        sys.exit(-1)
    # endif
# enddef


def gen_kill_script(script_name='/tmp/____kill_transmission.sh'):
    with open(script_name, 'w') as f_out:
        f_out.write('killall transmission-cli')
    # endwith
    # Give target script execute permissions
    os.chmod(script_name, 0o744)
# enddef

if __name__ == '__main__':
    parser  = argparse.ArgumentParser()
    parser.add_argument('--in_file',      help='Input csv file', type=str, default='/tmp/pirate_results.csv')
    parser.add_argument('--out_dir',      help='Output dir.', type=str, default='~/pirate_torrents')
    parser.add_argument('--min_seeders',  help='Minimum seeders count for the torrent to consider it for downloading.', type=int, default=1)
    parser.add_argument('--category',     help='Category to be specified.', type=str, default=None)
    parser.add_argument('--sub_category', help='Subcategory to be specified.', type=str, default=None)

    args    = parser.parse_args()

    in_file      = rp(args.__dict__['in_file'])
    out_dir      = rp(args.__dict__['out_dir'])
    min_seeders  = args.__dict__['min_seeders']
    sub_cat      = args.__dict__['sub_category']
    cat          = args.__dict__['category']

    if not in_file:
        print('--in_file is required !!')
        sys.exit(-1)
    # endif
    if not out_dir:
        print('--out_dir is required !!')
        sys.exit(-1)
    # endif

    chkfile(in_file)
    mkdir(out_dir)

    # Read csv file
    data_frame = pd.read_csv(in_file, delimiter=',')
    # Apply seeds condition
    data_frame = data_frame[data_frame['seeds'] >= min_seeders]

    if cat:
        if not any(data_frame.category.isin([cat])):
            print('Category should be one of {}'.format(data_frame.category.unique()))
            sys.exit(-1)
        # endif
    # endif
    if sub_cat:
        if not any(data_frame.subcat.isin([sub_cat])):
            print('Sub category should be one of {}'.format(data_frame.subcat.unique()))
            sys.exit(-1)
        # endif
    # endif

    # Write a temporary file for killing transmission-cli when it endsup downloading each torrent
    # This is a hack which has no work-around as such. Later we will move to some other
    # torrent client with more options
    kill_script='/tmp/____kill_transmission.sh'
    gen_kill_script(kill_script)

    # Start downloading
    for index, row in data_frame.iterrows():
        if cat and row['category'] != cat:
            continue
        # endif
        if sub_cat and row['subcat'] != sub_cat:
            continue
        # endif
        print('Downloading {}...'.format(row['title']))
        subprocess.call(['transmission-cli', '-er', '-f', kill_script, '-w', out_dir, row['magnet']])
    # endfor
# endif
