#!/usr/bin/python3
import urllib.error
import os
import sys
import tarfile
import shutil
import hashlib
import docker
import subprocess
import re

from urllib.request import urlopen
from jinja2 import FileSystemLoader, Environment, exceptions

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

    try:
        new_wp = tarfile.open(wp_latest['file'], 'r')
        new_wp.extractall()
        new_wp.close()

    except tarfile.TarError as tarerr:
        print('Unable to extract the tarball : %s' % tarerr)
        return False
    return True


def setup_wp_source_tree():
    home = os.getcwd()
    wp_root = '%s/wordpress' % home
    shutil.copy('./wp-config.php', './wordpress/wp-config.php')

    client = docker.from_env()
    client.containers.run('ubuntu:latest',
                          volumes={wp_root: {'bind': '/app'}},
                          command=['chown', '-R', ':daemon', '/app/'])


def create_php_fpm_image():
    bitnami_url = 'https://github.com/bitnami/bitnami-docker-php-fpm.git'
    bitnami_repo = 'bitnami-docker-php-fpm'
    php_fpm_version = '5.6'
    custom_files = ['php-fpm_entrypoint.sh', 'wp_automate.php']
    bitnami_dockerfile = '%s/%s' % (bitnami_repo, php_fpm_version)

    # First we cleanup the old repository
    try:
        if os.path.exists(bitnami_repo):
            shutil.rmtree(bitnami_repo)

    except PermissionError as err:
        print('Unable to remove old git repository : %s' % err)
        return False

    try:
        print('Cloning bitnami''s php-fpm image repository')
        subprocess.check_call(['git', 'clone', '%s' % bitnami_url],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as err:
        print('Unable to clone php-fpm git repository : %s' % err)
        print('Giving up')
        return False

    try:
        for file in custom_files:
            shutil.copy(file, '%s/%s/rootfs/%s' % (bitnami_repo,
                                                   php_fpm_version,
                                                   file))
    except OSError as err:
        print('Unable to copy custom files in repository : %s' % err)
        print('Giving up')
        return False

    print('Building new docker custom php-fpm image')

    version_regex = re.compile(r'BITNAMI_IMAGE_VERSION')
    entrypoint_regex = re.compile(r'^ENTRYPOINT')

    try:
        os.rename('%s/Dockerfile' % bitnami_dockerfile,
                  '%s/Dockerfile.old' % bitnami_dockerfile)
        with open('%s/Dockerfile.old' % bitnami_dockerfile, 'r') as dfile:
            lines = dfile.readlines()

        with open('%s/Dockerfile' % bitnami_dockerfile, 'w') as newfile:
            for line in lines:
                image_version = version_regex.search(line)
                entrypoint = entrypoint_regex.search(line)
                if entrypoint:
                    newfile.write('ENTRYPOINT ["/php-fpm_entrypoint.sh"]\n')
                    continue
                elif image_version:
                    full_image_version = image_version.string.split('"')[1]
                newfile.write(line)

    except OSError as err:
        print('Unable to find image version in Dockerfile.')
        print('Will use high level %s version' % php_fpm_version)
        print('the docker-compose.yml will need to be changed with :')
        print('php-fpm:\n  image: php-fpm:%s-custom' % php_fpm_version)
        full_image_version = php_fpm_version

    client = docker.from_env()
    client.images.build(path=bitnami_dockerfile,
                        tag='php-fpm:%s-custom' % full_image_version)


def _getvars(compose_file):

    regex = re.compile(r'MARIADB_.*')

    with open(compose_file, 'r') as compose:
        lines = compose.read()

    maria_vars = regex.findall(lines)
    maria_dict = {
            'mariadb_root_password': 'root-password',
            'mariadb_database': 'wordpress',
            'mariadb_user': 'wordpress',
            'mariadb_password': 'my-password',
            'mariadb_wp_user': 'wordpress',
            'mariadb_wp_password': 'wordpress',
            }
    for v in maria_vars:
        [key, item] = v.split('=')
        maria_dict[key.lower()] = item
    return maria_dict


def render_templates():
    env = Environment(loader=FileSystemLoader('.'),
                      lstrip_blocks=True, trim_blocks=True)

    templates = {
            'wp-config': 'wordpress',
            'wp_automate': '.',
            }
    context = _getvars('docker-compose.yml')

    for template in templates.keys():
        try:
            t = env.get_template('%s.template' % template)
            config = t.render(context)
            with open('%s/%s.php' % (templates[template],
                                     template), 'w') as conf:
                conf.write(config)

        except exceptions.TemplateNotFound as e:
            print('Could not load %s.template. '
                  'Using default %s.php' % (template, template))
            if template == 'wp-config':
                shutil.copy('%s.php' % template,
                            '%s/%s.php' % (templates[template], template))
    print('Custom files setup', end='')
    return True

if __name__ == '__main__':
    get_latest_wp()
    extract_wp_tarball()
    setup_wp_source_tree()
    create_php_fpm_image()
