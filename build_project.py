#!/usr/bin/python3
from urllib.request import urlopen
import urllib.error
import os
import tarfile
import shutil
import hashlib
import docker

wp_latest = {
    'file': 'latest.tar.gz',
    'url': 'https://wordpress.org/wordpress-latest.tar.gz',
    'md5': 'https://wordpress.org/wordpress-latest.tar.gz.md5',
    'dir': './wordpress',
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
        latest_md5 = urlopen(wp_latest['md5']).read().decode('UTF-8')

        # Check if we don't already have the latest file
        if os.path.exists(wp_latest['file']):
            if check_md5_ok(wp_latest['file'], latest_md5):
                print('We have the latest %s' % wp_latest['file'])
                return True
            else:
                print('Current %s MD5 do not match' % wp_latest['file'])

        # Either we don't have a file or the MD5 doesn't match
        # Get a new one
        with urlopen(wp_latest['url']) as tarball_resp:
            print('Downloading new %s' % wp_latest['file'])
            with open(wp_latest['file'], 'wb') as tarball:
                tarball.write(tarball_resp.read())

        if check_md5_ok(wp_latest['file'], latest_md5):
            print('We have the latest %s' % wp_latest['file'])
            return True
        else:
            print('Unable to get %s that matches %s' % (wp_latest['file'],
                                                        latest_md5))
            return False

    except (urllib.error.URLError,
            urllib.error.HTTPError,
            ConnectionResetError) as err:
        print('Unable to fetch MD5 value : %s' % err)
        print('Using the current file')
        return

def extract_wp_tarball():

    # First we cleanup the old wp dir
    try:
        if os.path.exists(wp_latest['dir']):
            shutil.rmtree(wp_latest['dir'])

    except PermissionError as err:
        print('Unable to remove old %s directory : %s' % (wp_latest['dir'],
                                                          err))
        return False

    new_wp = tarfile.open(wp_latest['file'], 'r')
    try:
        new_wp.extractall()
        new_wp.close()

    except tarfile.TarError as tarerr:
        print('Unable to extract the tarball : %s' % tarerr)
        return False
    return True

def setup_wp_source_tree():
    home = os.getcwd()
    wp_root = '%s/wordpress' % home
    shutil.copy('./wp-config.php','./wordpress/wp-config.php')

    client = docker.from_env()
    client.containers.run('ubuntu:latest', 
                         volumes={wp_root:{'bind': '/app'}},
                         command=['chown','-R',':daemon','/app/'])

if __name__ == '__main__':
    get_latest_wp()
    extract_wp_tarball()
    setup_wp_source_tree()
