#!/usr/bin/env python3
#
# Author: Vikas Chouhan (presentisgood@gmail.com).

import os
import sys
import argparse
import libtorrent as lt
import time

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


if __name__ == '__main__':
    parser  = argparse.ArgumentParser()
    parser.add_argument('--torrent',      help='Magnet link', type=str, default=None)
    parser.add_argument('--out_dir',      help='Output dir.', type=str, default='~/pirate_torrents')
    parser.add_argument('--sequential',   help='Download sequentially.', action='store_true')

    args    = parser.parse_args()

    torrent_link = args.__dict__['torrent']
    out_dir      = rp(args.__dict__['out_dir'])
    sequential   = args.__dict__['sequential']

    if not torrent_link:
        print('--torrent is required !!')
        sys.exit(-1)
    # endif
    if not out_dir:
        print('--out_dir is required !!')
        sys.exit(-1)
    # endif

    mkdir(out_dir)

    # Download params
    params = {
        'save_path': out_dir,
        'storage_mode': lt.storage_mode_t(2),
        'auto_managed': True,
        'file_priorities': [0]*5,
    }


    sess = lt.session()
    handle = lt.add_magnet_uri(sess, torrent_link, params)
    handle.set_sequential_download(sequential)
    print('downloading metadata...')
    while not handle.has_metadata():
        time.sleep(2)
    # endwhile

    print('got metadata, starting torrent download...')
    while (handle.status().state != lt.torrent_status.seeding):
        print('{}% done'.format(int(handle.status().progress*100)), end='\r')
        time.sleep(2)
    # endwhile
# endif
