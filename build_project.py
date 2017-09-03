#!/usr/bin/python3
import urllib.request
import os
import hashlib

wp_latest = {
    'file' : 'latest.tar.gz',
    'url' : 'https://wordpress.org/wordpress-latest.tar.gz',
    'md5' : 'https://wordpress.org/wordpress-latest.tar.gz.md5',
    }

def check_md5_ok(file_to_check, md5):
    '''
    Verify the MD5 checksum of a file
    The file is expected to exist
    '''
    with open(file_to_check, 'rb') as f:
        checksum = hashlib.md5(f.read()).hexdigest()
    if checksum == md5:
        return True
    else:
        return False

def get_latest_wp():

    try:
        # Get the MD5 of the latest file first
        with urllib.request.urlopen(wp_latest['md5']) as md5_resp:
            latest_md5 = md5_resp.read().decode('UTF-8')

        # Check if we don't already have the latest file
        if os.path.exists(wp_latest['file']) :
            if check_md5_ok(wp_latest['file'],latest_md5):
                print('We have the latest %s' % wp_latest['file'])
                return True
            else:
                print('Current %s MD5 do not match' % wp_latest['file'])

        # Either we don't have a file or the MD5 doesn't match
        # Get a new one
        with urllib.request.urlopen(wp_latest['url']) as tarball_resp:
            print('Downloading new %s' % wp_latest['file'])
            with open(wp_latest['file'], 'wb') as tarball:
                tarball.write(tarball_resp.read())

        if check_md5_ok(wp_latest['file'],latest_md5):
            print('We have the latest %s' % wp_latest['file'])
            return True
        else:
            print('Unable to get %s that matches %s' % (latest_wp['file'],
                                                        latest_md5))
            return False

    except (urllib.error.URLError,
            urllib.error.HTTPError,
            ConnectionResetError) as err:
        print('Unable to fetch MD5 value : %s' % err)
        print('Using the current file')
        return



if __name__ == '__main__':
    get_latest_wp()