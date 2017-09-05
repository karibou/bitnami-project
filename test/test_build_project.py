import unittest
import build_project
import sys
import os
import shutil
import tarfile
import subprocess
import tempfile
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
            dfile.write('CMD ["/run.sh"]\n')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.workdir)

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
        self.assertEquals(output, 'Unable to extract the tarball :')

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
        ret = build_project.create_php_fpm_image()
        self.assertFalse(ret)

    @patch('build_project.os.path.exists', return_value=False)
    @patch('build_project.subprocess.check_call')
    @patch('build_project.shutil.copy')
    @patch('build_project.docker.from_env')
    def test_git_repo_dockerfile_fix_with_exception(self, m_docker, m_copy,
                                                    m_sub, m_exists):

        os.chdir(self.workdir)
        m_docker.return_value = self.fake_docker
        ret = build_project.create_php_fpm_image()
        self.assertEquals(self.fake_docker.images.build.call_args[1]['tag'],
                          'php-fpm:5.6.31-r0-custom')
        os.chdir(self.root)
