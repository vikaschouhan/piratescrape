#
# NOTE: Originally authored by Arpit Choudhary under MIT License.
#       Modified for cmd line usage by Vikas Chouhan.

import os
import requests
import sys
import re
from   bs4 import BeautifulSoup
from   datetime import datetime, timedelta
import argparse
import json

EMPTY_LIST = []
BASE_URL = None
PROXY = None

# Translation table for sorting filters
sort_filters = {
    'title_asc': 1,
    'title_desc': 2,
    'time_desc': 3,
    'time_asc': 4,
    'size_desc': 5,
    'size_asc': 6,
    'seeds_desc': 7,
    'seeds_asc': 8,
    'leeches_desc': 9,
    'leeches_asc': 10,
    'uploader_asc': 11,
    'uploader_desc': 12,
    'category_asc': 13,
    'category_desc': 14
}

def set_base_url(url):
    print('Setting piratebay url to {}'.format(url))
    global BASE_URL
    BASE_URL = url
# enddef

def set_proxy(proxy):
    print('Setting proxy to {}'.format(proxy))
    global PROXY
    PROXY = proxy
# enddef

def request_get(url):
    if PROXY == None:
        return requests.get(url)
    else:
        return requests.get(url, proxies=PROXY)
    # endif
# enddef

def jsonify(obj):
    def date_converter(o):
        if isinstance(o, datetime):
            return o.__str__()
        # endif
    # enddef
    return json.loads(json.dumps(obj, default=date_converter))
# enddef


def top_torrents(cat=0, sort=None):
    '''
    Returns top torrents
    '''

    sort_arg = sort if sort in sort_filters else ''

    if cat == 0:
        url = BASE_URL + 'top/' + 'all/' + str(sort_arg)
    else:
        url = BASE_URL + 'top/' + str(cat) + '/' + str(sort_arg)
    # endif
    return jsonify(parse_page(url, sort=sort_arg)), 200
# enddef


def top48h_torrents(cat=0, sort=None):
    '''
    Returns top torrents last 48 hrs
    '''

    sort_arg = sort if sort in sort_filters else ''

    if cat == 0:
        url = BASE_URL + 'top/48h' + 'all/'
    else:
        url = BASE_URL + 'top/48h' + str(cat)
    # endif

    return jsonify(parse_page(url, sort=sort_arg)), 200
# enddef


def recent_torrents(page=0, sort=None):
    '''
    This function implements recent page of TPB
    '''
    sort_arg = sort if sort in sort_filters else ''

    url = BASE_URL + 'recent/' + str(page)
    return jsonify(parse_page(url, sort=sort_arg)), 200
# enddef


def search_torrents(term=None, page=0, sort=None):
    '''
    Searches TPB using the given term. If no term is given, defaults to recent.
    '''

    sort_arg = sort_filters[sort] if sort in sort_filters else ''

    url = BASE_URL + 'search/' + str(term) + '/' + str(page) + '/' + str(sort_arg)
    return jsonify(parse_page(url)), 200
# enddef


def parse_page(url, sort=None):
    '''
    This function parses the page and returns list of torrents
    '''
    data = request_get(url).text
    soup = BeautifulSoup(data, 'lxml')
    table_present = soup.find('table', {'id': 'searchResult'})
    if table_present is None:
        return EMPTY_LIST
    # enddef
    titles = parse_titles(soup)
    magnets = parse_magnet_links(soup)
    times, sizes, uploaders = parse_description(soup)
    seeders, leechers = parse_seed_leech(soup)
    cat, subcat = parse_cat(soup)
    torrents = []
    for torrent in zip(titles, magnets, times, sizes, uploaders, seeders, leechers, cat, subcat):
        torrents.append({
            'title': torrent[0],
            'magnet': torrent[1],
            'time': convert_to_date(torrent[2]),
            'size': convert_to_bytes(torrent[3]),
            'uploader': torrent[4],
            'seeds': int(torrent[5]),
            'leeches': int(torrent[6]),
            'category': torrent[7],
            'subcat': torrent[8],
        })
    # endfor

    if sort:
        sort_params = sort.split('_')
        torrents = sorted(torrents, key=lambda k: k.get(sort_params[0]), reverse=sort_params[1].upper() == 'DESC')
    # endif

    return torrents
# enddef


def parse_magnet_links(soup):
    '''
    Returns list of magnet links from soup
    '''
    magnets = soup.find('table', {'id': 'searchResult'}).find_all('a', href=True)
    magnets = [magnet['href'] for magnet in magnets if 'magnet' in magnet['href']]
    return magnets
# enddef


def parse_titles(soup):
    '''
    Returns list of titles of torrents from soup
    '''
    titles = soup.find_all(class_='detLink')
    titles[:] = [title.get_text() for title in titles]
    return titles
# enddef


def parse_description(soup):
    '''
    Returns list of time, size and uploader from soup
    '''
    description = soup.find_all('font', class_='detDesc')
    description[:] = [desc.get_text().split(',') for desc in description]
    times, sizes, uploaders = map(list, zip(*description))
    times[:] = [time.replace(u'\xa0', u' ').replace('Uploaded ', '') for time in times]
    sizes[:] = [size.replace(u'\xa0', u' ').replace(' Size ', '') for size in sizes]
    uploaders[:] = [uploader.replace(' ULed by ', '') for uploader in uploaders]
    return times, sizes, uploaders
# enddef


def parse_seed_leech(soup):
    '''
    Returns list of numbers of seeds and leeches from soup
    '''
    slinfo = soup.find_all('td', {'align': 'right'})
    seeders = slinfo[::2]
    leechers = slinfo[1::2]
    seeders[:] = [seeder.get_text() for seeder in seeders]
    leechers[:] = [leecher.get_text() for leecher in leechers]
    return seeders, leechers
# enddef


def parse_cat(soup):
    '''
    Returns list of category and subcategory
    '''
    cat_subcat = soup.find_all('center')
    cat_subcat[:] = [c.get_text().replace('(', '').replace(')', '').split() for c in cat_subcat]
    cat = [cs[0] for cs in cat_subcat]
    subcat = [' '.join(cs[1:]) for cs in cat_subcat]
    return cat, subcat
# enddef


def convert_to_bytes(size_str):
    '''
    Converts torrent sizes to a common count in bytes.
    '''
    size_data = size_str.split()

    multipliers = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB']

    size_magnitude = float(size_data[0])
    multiplier_exp = multipliers.index(size_data[1])
    size_multiplier = 1024 ** multiplier_exp if multiplier_exp > 0 else 1

    return size_magnitude * size_multiplier
# enddef


def convert_to_date(date_str):
    '''
    Converts the dates into a proper standardized datetime.
    '''

    date_format = None

    if re.search('^[0-9]+ min(s)? ago$', date_str.strip()):
        minutes_delta = int(date_str.split()[0])
        torrent_dt = datetime.now() - timedelta(minutes=minutes_delta)
        date_str = '{}-{}-{} {}:{}'.format(torrent_dt.year, torrent_dt.month, torrent_dt.day, torrent_dt.hour, torrent_dt.minute)
        date_format = '%Y-%m-%d %H:%M'

    elif re.search('^[0-9]*-[0-9]*\s[0-9]+:[0-9]+$', date_str.strip()):
        today = datetime.today()
        date_str = '{}-'.format(today.year) + date_str
        date_format = '%Y-%m-%d %H:%M'
    
    elif re.search('^Today\s[0-9]+\:[0-9]+$', date_str):
        today = datetime.today()
        date_str = date_str.replace('Today', '{}-{}-{}'.format(today.year, today.month, today.day))
        date_format = '%Y-%m-%d %H:%M'
    
    elif re.search('^Y-day\s[0-9]+\:[0-9]+$', date_str):
        today = datetime.today() - timedelta(days=1)
        date_str = date_str.replace('Y-day', '{}-{}-{}'.format(today.year, today.month, today.day))
        date_format = '%Y-%m-%d %H:%M'

    else:
        date_format = '%m-%d %Y'

    # endif

    return datetime.strptime(date_str, date_format)
# enddef
