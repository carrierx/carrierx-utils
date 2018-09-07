#!/bin/env python


import argparse
from copy import deepcopy
from itertools import groupby
import json
import sys

import requests


def main():
    api_headers = {'Content-type': 'application/json'}

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', help='fcc4d api username:password', dest='api_auth')
    parser.add_argument(
        '--api-base-url', 
        help='alternative api url', 
        dest='api_base_url', 
        default='https://api.carrierx.com/core/v2'
    )
    parser.add_argument('--prefix', help='run only on one prefix', dest='prefix')
    parser.add_argument('--filter', help='run only on one filter', dest='filter')
    parser.add_argument('--infile', help='read number prefixes from file', dest='infile')
    parser.add_argument('--trunk_group_sid', help='trunk_group_sid to assign', dest='trunk_group_sid')
    parser.add_argument('--callback_url', help='callback_url to assign', dest='callback_url')
    parser.add_argument('--progress', action='store_true', help='show progress while querying api')
    args = parser.parse_args()
    try:
        api_auth = tuple(args.api_auth.split(':'))
    except:
        parser.print_help()
        sys.exit(1)

    account_dids = []
    account_dids_per_trunk_group = {}

    if args.filter:
        wanted_filters = [args.filter]
    elif args.prefix:
        wanted_filters = ['phonenumber like "{0}%"'.format(args.prefix)]
    elif args.infile:
        wanted_filters = []
        with open(args.infile) as fh:
            for line in fh:
                wanted_filters.append('phonenumber like "{0}%"'.format(line.rstrip()))
    else:
        wanted_filters = [None]

    tg_map = {}
    r = requests.get(
        url='{0}/trunk_groups'.format(args.api_base_url),
        auth=api_auth,
        headers={'Content-Type': 'application/json'},
    )
    data = r.json()
    for i in data['items']:
        tg_map[i['trunk_group_sid']] = i['name']

    for filter in wanted_filters:
        has_more = True
        offset = 0
        while has_more:
            params = {
                'offset': offset,
            }
            if filter:
                params['filter'] = filter

            r = requests.get(
                url='{0}/dids/inventory'.format(args.api_base_url),
                auth=api_auth,
                headers=api_headers,
                params=params,
            )
            data = r.json()

            if r.status_code != 200:
                print("Error calling API: {0}".format(data))
                sys.exit(2)

            for i in data['items']:
                wanted_i = {
                    'phonenumber': i['phonenumber']
                }

                if args.trunk_group_sid is not None:
                    wanted_i['trunk_group_sid'] = args.trunk_group_sid
                if args.callback_url is not None:
                    wanted_i['callback_url'] = args.callback_url

                r = requests.post(
                    url='{0}/dids'.format(args.api_base_url),
                    auth=api_auth,
                    headers=api_headers,
                    data=json.dumps(wanted_i),
                )

                if r.status_code == 200:
                    if args.progress:
                        dot('.')
                else:
                    dot('@')
                    print("Error POSTing: {0}: {1}".format(i['phonenumber'], r.content))
                        
            has_more = (data['count'] == data['limit'])
            offset = data['offset'] + data['limit']


def dot(char='.'):
    sys.stdout.write(char)
    sys.stdout.flush()


if __name__ == '__main__':
    main()
