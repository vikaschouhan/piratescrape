#!/usr/bin/env python3
import pandas as pd
from   torrent_utils import *
import os

def chk_onion_url(url):
    if os.path.splitext(url)[1] == '.onion':
        return True
    # endif
    return False
# enddef

if __name__ == '__main__':
    parser  = argparse.ArgumentParser()
    parser.add_argument('--search',    help='String to be searched for.', type=str, default=None)
    parser.add_argument('--base_url',  help='Base url for piratebay website.', type=str, default='https://thepiratebay.org/')
    parser.add_argument('--out_file',  help='Output csv file', type=str, default='/tmp/pirate_results.csv')
    parser.add_argument('--max_pages', help='Maximum number of pages to search for.', type=int, default=1)
    parser.add_argument('--use_onion', help='Use onion website.', action='store_true')

    args    = parser.parse_args()

    search_str = args.__dict__['search']
    base_url   = args.__dict__['base_url']
    out_file   = args.__dict__['out_file']
    max_pages  = args.__dict__['max_pages']
    use_onion  = args.__dict__['use_onion']

    if not search_str:
        print('--search is required !!')
        sys.exit(-1)
    # endif
    if not base_url:
        print('--base_url is required !!')
        sys.exit(-1)
    else:
        if use_onion:
            base_url = base_url if chk_onion_url(base_url) else 'http://uj3wazyk5u4hnvtk.onion/'
            set_proxy({'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'})
        # endif
        set_base_url(base_url)
    # endif
    if not out_file:
        print('--out_file is required !!')
        sys.exit(-1)
    # endif

    torrent_list = []
    for page_t in range(max_pages):
        print('Getting page={}'.format(page_t), end='\r')
        json_t = search_torrents(search_str, page=page_t)
        if json_t[1] != 200:
            break
        # endif
        torrent_list = torrent_list + json_t[0]

        if len(torrent_list) == 0:
            print('Nothing found !!')
            sys.exit(-1)
        # endif
    # endfor

    data_frame = pd.DataFrame()
    headers = list(torrent_list[0].keys())
    # Add columns
    for header_t in headers:
        data_frame[header_t] = [x[header_t] for x in torrent_list]
    # endfor

    # Write to csv file
    print('Writing to {}'.format(out_file))
    data_frame.to_csv(out_file)
# endif
