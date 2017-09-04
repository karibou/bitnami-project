import unittest
import build_project
from unittest.mock import patch, MagicMock


class BuildProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.fake_file = MagicMock()
        self.fake_md5_hash = MagicMock()
        self.fake_md5_hash.add_spec('hexdigest')
        self.fake_md5_query = MagicMock()
        self.fake_md5_query.add_spec('read')

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
