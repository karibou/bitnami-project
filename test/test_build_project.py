import unittest
import build_project
import sys
import os
import shutil
import tarfile
import subprocess
import tempfile
import argparse
from unittest.mock import patch, MagicMock


class BuildProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.wp_latest = build_project.wp_latest
        self.root = os.getcwd()
        self.fake_file = MagicMock()
        self.fake_md5_hash = MagicMock()
        self.fake_md5_hash.add_spec('hexdigest')
        self.fake_md5_query = MagicMock()
        self.fake_md5_query.add_spec('read')
        self.fake_tarfile = MagicMock()
        self.fake_docker = MagicMock()
        self.workdir = tempfile.mkdtemp()
        os.makedirs('%s/bitnami-docker-php-fpm/5.6' % self.workdir)
        self.Dockerfile = os.path.join(self.workdir,
                                       'bitnami-docker-php-fpm/5.6',
                                       'Dockerfile')
        with open(self.Dockerfile, 'w') as dfile:
            dfile.write('COPY rootfs /\n')
            dfile.write('    BITNAMI_IMAGE_VERSION="5.6.31-r0" \\\n')
            dfile.write('ENTRYPOINT ["/php-fpm_entrypoint.sh"]\n')
        self.compose = os.path.join(self.workdir, 'docker-compose.yml')
        with open(self.compose, 'w') as cfile:
            cfile.write('start\nMARIADB_USER=0xdead\n'
                        'MARIADB_PASSWORD=0xbeef\nend\n')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.workdir)

    def tearDown(self):
        os.chdir(self.root)
        if os.path.exists(os.path.join(self.workdir, 'wordpress')):
            shutil.rmtree(os.path.join(self.workdir, 'wordpress'))

    @patch('builtins.open')
    @patch('build_project.hashlib.md5')
    def test_check_md5_ok(self, m_md5, m_open):
        '''
        Check test with same MD5
        '''
        m_open.return_value = self.fake_file
        self.fake_md5_hash.hexdigest.return_value = 'a'
        m_md5.return_value = self.fake_md5_hash
        ret = build_project.check_md5_ok(None, 'a')
        self.assertTrue(ret)

    @patch('builtins.open')
    @patch('build_project.hashlib.md5')
    def test_check_md5_nok(self, m_md5, m_open):
        '''
        Check test with different MD5
        '''
        m_open.return_value = self.fake_file
        self.fake_md5_hash.hexdigest.return_value = 'b'
        m_md5.return_value = self.fake_md5_hash
        ret = build_project.check_md5_ok(None, 'a')
        self.assertFalse(ret)

    @patch('build_project.urlopen')
    @patch('build_project.os.path.exists', return_value=True)
    @patch('build_project.check_md5_ok', return_value=True)
    def test_get_latest_has_file_same_md5(self, m_md5_ok,
                                          m_path_exists, m_urlopen):
        '''
        Check latest when file exist and has same md5
        '''
        self.fake_md5_query.read.return_value = b'abc'
        m_urlopen.return_value = self.fake_md5_query
        ret = build_project.get_latest_wp()
        self.assertTrue(ret)

    @patch('build_project.urlopen')
    @patch('build_project.os.path.exists', return_value=True)
    @patch('build_project.check_md5_ok', side_effect=(False, True))
    @patch('builtins.open')
    def test_get_latest_has_file_diff_md5(self, m_open, m_md5_ok,
                                          m_path_exists, m_urlopen):
        '''
        Check latest when file exist and has different md5
        '''
        m_open.return_value = self.fake_file
        ret = build_project.get_latest_wp()
        self.assertTrue(ret)

    @patch('build_project.urlopen')
    @patch('build_project.os.path.exists', return_value=True)
    @patch('build_project.check_md5_ok', side_effect=(False, False))
    @patch('builtins.open')
    def test_get_latest_has_file_diff_md5_twice(self, m_open, m_md5_ok,
                                                m_path_exists, m_urlopen):
        '''
        Check latest when file exist and has different md5 twice
        '''
        m_open.return_value = self.fake_file
        ret = build_project.get_latest_wp()
        self.assertFalse(ret)

    @patch('build_project.urlopen', side_effect=ConnectionResetError)
    def test_get_latest_exception(self, m_urlopen):
        '''
        Test exception handling
        '''
        ret = build_project.get_latest_wp()
        self.assertFalse(ret)

    @patch('build_project.tarfile.open')
    @patch('build_project.os.path.exists', return_value=True)
    @patch('build_project.shutil.rmtree')
    def test_extract_wp_tarball(self, m_rmtree, m_exists, m_tarfile):
        '''
        Test tarball cleanup and extraction
        '''
        m_tarfile.return_value = self.fake_tarfile
        ret = build_project.extract_wp_tarball()
        m_rmtree.assert_called_once_with(self.wp_latest['dir'])
        m_tarfile.assert_called_once_with(self.wp_latest['file'], 'r')
        self.fake_tarfile.extractall.assert_called_once_with()
        self.fake_tarfile.close.assert_called_once_with()

    @patch('build_project.os.path.exists', return_value=True)
    @patch('build_project.shutil.rmtree', side_effect=PermissionError)
    def test_extract_wp_tarball_cleanup_error(self, m_rmtree, m_exists):
        '''
        Test cleanup exception handling
        '''
        ret = build_project.extract_wp_tarball()
        self.assertFalse(ret)

    @patch('build_project.tarfile.open', side_effect=tarfile.TarError)
    @patch('build_project.os.path.exists', return_value=False)
    def test_extract_wp_tarball_tar_exception(self, m_exists, m_tarfile):
        '''
        Test tarball cleanup and extraction
        '''
        ret = build_project.extract_wp_tarball()
        self.assertFalse(ret)
        output = sys.stdout.getvalue().strip()
        self.assertEquals(output, 'Extracting new tarball\n'
                          'Unable to extract the tarball :')

    @patch('build_project.os.getcwd', return_value='/home')
    @patch('build_project.docker.from_env')
    def test_setup_wp_tree(self, m_docker, m_cwd):
        '''
        Test wp source tree setup
        '''
        m_docker.return_value = self.fake_docker
        ret = build_project.setup_wp_source_tree()
        self.assertEquals(self.fake_docker.containers.run.call_count, 1)

    @patch('build_project.os.path.exists', return_value=True)
    @patch('build_project.shutil.rmtree', side_effect=PermissionError)
    def test_git_repo_cleanup_with_exception(self, m_rmtree, m_exists):
        '''
        Test git repo cleanup with exception handling
        '''
        ret = build_project.create_php_fpm_image()
        self.assertFalse(ret)

    @patch('build_project.os.path.exists', return_value=False)
    @patch('build_project.subprocess.check_call',
           side_effect=subprocess.CalledProcessError(1, 'error'))
    def test_git_repo_git_clone_with_exception(self, m_sub, m_exists):
        '''
        Test git repo cleanup with exception handling
        '''
        ret = build_project.create_php_fpm_image()
        self.assertFalse(ret)

    @patch('build_project.os.path.exists', return_value=False)
    @patch('build_project.subprocess.check_call')
    @patch('build_project.shutil.copy', side_effect=OSError)
    def test_git_repo_customfile_copy_with_exception(self,
                                                     m_copy, m_sub, m_exists):
        '''
        Test git repo creation, custom file copy with exception
        '''
        ret = build_project.create_php_fpm_image()
        self.assertFalse(ret)

    @patch('build_project.os.path.exists', return_value=False)
    @patch('build_project.subprocess.check_call')
    @patch('build_project.shutil.copy')
    @patch('build_project.docker.from_env')
    def test_git_repo_dockerfile_fix_with_exception(self, m_docker, m_copy,
                                                    m_sub, m_exists):
        '''
        Test Dockerfile modification in git repo with exception
        '''
        os.chdir(self.workdir)
        m_docker.return_value = self.fake_docker
        ret = build_project.create_php_fpm_image()
        self.assertEquals(self.fake_docker.images.build.call_args[1]['tag'],
                          'php-fpm:5.6.31-r0-custom')

    @patch('build_project.os.path.exists', return_value=False)
    @patch('build_project.subprocess.check_call')
    @patch('build_project.shutil.copy')
    @patch('build_project.docker.from_env')
    def test_git_repo_custom_files_with_multisite(self, m_docker, m_copy,
                                                  m_sub, m_exists):
        '''
        Test custom files copy with multisite enabled and exception
        '''
        os.chdir(self.workdir)
        ret = build_project.create_php_fpm_image(True)
        self.assertEquals(m_copy.call_count, 3)

    def test_getvars(self):
        '''
        Test _getvars() template substitution
        '''
        os.chdir(self.workdir)
        ret = build_project._getvars('docker-compose.yml')
        self.assertEquals(ret['mariadb_user'], '0xdead')
        self.assertEquals(ret['mariadb_password'], '0xbeef')

    def test_template_rendering(self):
        '''
        Test template rendering for wp-config.php and wp_automate.php
        '''
        os.mkdir(os.path.join(self.workdir, 'wordpress'))
        shutil.copy('wp_automate.template', self.workdir)
        shutil.copy('wp-config.template', self.workdir)
        os.chdir(self.workdir)
        ret = build_project.render_templates()
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wp_automate.php')))
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wordpress',
                                                    'wp-config.php')))
        with open(os.path.join(self.workdir, 'wp_automate.php')) as automate:
            lines = automate.read()
        self.assertRegexpMatches(lines, r'0xdead')
        with open(os.path.join(self.workdir, 'wordpress', 'wp-config.php')
                  ) as config:
            lines = config.read()
        self.assertRegexpMatches(lines, r'0xbeef')
        self.assertNotRegex(lines, r'MULTISITE')

    def test_template_rendering_multisite(self):
        '''
        Test multisite template rendering for wp-config.php and wp_automate.php
        '''
        os.mkdir(os.path.join(self.workdir, 'wordpress'))
        shutil.copy('wp_automate.template', self.workdir)
        shutil.copy('wp-config.template', self.workdir)
        shutil.copy('.htaccess.template', self.workdir)
        os.chdir(self.workdir)
        ret = build_project.render_templates(True)
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wp_automate.php')))
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wordpress',
                                                    'wp-config.php')))
        with open(os.path.join(self.workdir, 'wp_automate.php')) as automate:
            lines = automate.read()
        self.assertRegexpMatches(lines, r'0xdead')
        with open(os.path.join(self.workdir, 'wordpress', 'wp-config.php')
                  ) as config:
            lines = config.read()
        self.assertRegexpMatches(lines, r'0xbeef')
        self.assertRegex(lines, r'MULTISITE')
        self.assertRegex(lines, r"SUBDOMAIN_INSTALL', false")
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wordpress',
                                                    '.htaccess')))

    def test_template_rendering_multisite_subdomain(self):
        '''
        Test multisite template rendering with subdomain for wp-config.php
        '''
        os.mkdir(os.path.join(self.workdir, 'wordpress'))
        shutil.copy('wp_automate.template', self.workdir)
        shutil.copy('wp-config.template', self.workdir)
        os.chdir(self.workdir)
        ret = build_project.render_templates(True, True)
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wp_automate.php')))
        self.assertTrue(os.path.exists(os.path.join(self.workdir,
                                                    'wordpress',
                                                    'wp-config.php')))
        with open(os.path.join(self.workdir, 'wp_automate.php')) as automate:
            lines = automate.read()
        self.assertRegexpMatches(lines, r'0xdead')
        with open(os.path.join(self.workdir, 'wordpress', 'wp-config.php')
                  ) as config:
            lines = config.read()
        self.assertRegexpMatches(lines, r'0xbeef')
        self.assertRegex(lines, r'MULTISITE')
        self.assertRegex(lines, r"SUBDOMAIN_INSTALL', true")

    def test_missing_rendering_templates(self):
        '''
        Test missing template error handling
        '''
        os.chdir(self.workdir)
        ret = build_project.render_templates(False, False)
        self.assertFalse(ret)

    @patch('build_project.get_latest_wp', return_value=True)
    @patch('build_project.extract_wp_tarball', return_value=True)
    @patch('build_project.setup_wp_source_tree', return_value=True)
    @patch('build_project.render_templates', return_value=True)
    @patch('build_project.create_php_fpm_image', return_value=True)
    @patch('build_project._getvars', return_value={'mariadb_wp_user': 'a',
                                                   'mariadb_wp_password': 'b'})
    def test_main(self, m_getvars, m_image, m_templates, m_source,
                  m_tarball, m_latest):
        '''
        Test main execution logic
        '''
        build_project.sys.argv = ['main', ]
        ret = build_project.main()
        m_getvars.assert_called_once_with('docker-compose.yml')
        m_image.assert_called_once_with()
        m_templates.assert_called_once_with(False, False)
        m_source.assert_called_once_with()
        m_tarball.assert_called_once_with()
        m_latest.assert_called_once_with()

    @patch('argparse.ArgumentParser.parse_args')
    @patch('build_project.get_latest_wp', return_value=True)
    @patch('build_project.extract_wp_tarball', return_value=True)
    @patch('build_project.setup_wp_source_tree', return_value=True)
    @patch('build_project.render_templates', return_value=True)
    @patch('build_project.create_php_fpm_image', return_value=True)
    @patch('build_project._getvars', return_value={'mariadb_wp_user': 'a',
                                                   'mariadb_wp_password': 'b'})
    def test_main_alt(self, m_getvars, m_image, m_templates, m_source,
                      m_tarball, m_latest, m_argparse):
        '''
        Test main execution logic with alternate on
        '''
        build_project.sys.argv = ['main', '-a']
        args = argparse.Namespace()
        args.alternate = True
        args.multisite = False
        args.subdomain = False
        m_argparse.return_value = args
        ret = build_project.main()
        m_getvars.assert_called_once_with('docker-compose.yml')
        m_image.assert_not_called
        m_templates.assert_called_once_with(False, False)
        m_source.assert_called_once_with()
        m_tarball.assert_called_once_with()
        m_latest.assert_called_once_with()

    @patch('build_project.get_latest_wp', return_value=True)
    @patch('build_project.extract_wp_tarball', return_value=True)
    @patch('build_project.setup_wp_source_tree', return_value=True)
    @patch('build_project.render_templates', return_value=True)
    @patch('build_project.create_php_fpm_image', return_value=True)
    @patch('build_project._getvars', return_value={'mariadb_wp_user': 'a',
                                                   'mariadb_wp_password': 'b'})
    def test_main_multisite(self, m_getvars, m_image, m_templates, m_source,
                            m_tarball, m_latest):
        '''
        Test main execution logic with multisite on
        '''
        build_project.sys.argv = ['main', '-m']
        ret = build_project.main()
        m_getvars.assert_called_once_with('docker-compose.yml')
        m_image.assert_called_once_with()
        m_templates.assert_called_once_with(True, False)
        m_source.assert_called_once_with()
        m_tarball.assert_called_once_with()
        m_latest.assert_called_once_with()
