#!/usr/bin/python3
import urllib.request
import os
import hashlib

wp_latest = {
    'file' : 'latest.tar.gz',
    'url' : 'https://wordpress.org/wordpress-latest.tar.gz',
    'md5' : 'https://wordpress.org/wordpres-latest.tar.gz.md5',
    }

def get_latest_wp():

    # First we check if we're working on the latest tarball
    if os.path.exists(wp_latest['file']) :
        with open(wp_latest['file'], 'rb') as current_latest:
            checksum = hashlib.md5(current_latest.read()).hexdigest()

        try:
            with urllib.request.urlopen(wp_latest['md5']) as response:
                latest_md5 = response.read().decode('UTF-8')
            if checksum == latest_md5:
                print('We have the latest')
                return

        except (urllib.error.URLError,
                urllib.error.HTTPError,
                ConnectionResetError) as err:
            print('Unable to fetch MD5 value : %s' % err)
            print('Using the current file')
            return


    # If not the latest or no file found
    # tarball = requests.get(wp_latest['url'])

if __name__ == '__main__':
    get_latest_wp()
