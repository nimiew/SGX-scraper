import unittest
import download
import os
from datetime import datetime

class TestDownload(unittest.TestCase):
    def test_assert_WEBPXTICK_DT_filename(self):
        self.assertTrue(download.assert_WEBPXTICK_DT_filename("WEBPXTICK_DT-20040501.zip"))
        self.assertTrue(download.assert_WEBPXTICK_DT_filename("WEBPXTICK_DT-20050302.gz"))
        self.assertFalse(download.assert_WEBPXTICK_DT_filename("WEBPXTICK_DT-20050302.abc"))
        self.assertFalse(download.assert_WEBPXTICK_DT_filename("WEBPXTICK_DT-20050302"))
        self.assertFalse(download.assert_WEBPXTICK_DT_filename("WEBPXTICK_DT-200530302.zip"))
        self.assertFalse(download.assert_WEBPXTICK_DT_filename("WEBPXTICK_DT-2005302.gz"))
    
    def test_assert_TC_filename(self):
        self.assertTrue(download.assert_TC_filename("TC_20040501.txt"))
        self.assertFalse(download.assert_TC_filename("TC_2004001.txt"))
        self.assertFalse(download.assert_TC_filename("TC_200403501.txt"))
        self.assertFalse(download.assert_TC_filename("TC_20040501.abc"))
        self.assertFalse(download.assert_TC_filename("TC_20040501"))

    def test_get_date_string(self):
        self.assertEquals(download.get_date_string("TC_20040501.txt"), "20040501")
        self.assertEquals(download.get_date_string("WEBPXTICK_DT-20040503.zip"), "20040503")
    
    def test_get_filename(self):
        good_code = "2756"
        bad_code = "2750"
        good_url = f"https://links.sgx.com/1.0.0/derivatives-historical/{good_code}/WEBPXTICK_DT.zip"
        bad_url = f"https://links.sgx.com/1.0.0/derivatives-historical/{bad_code}/WEBPXTICK_DT.zip"
        self.assertEquals(download.get_filename(good_url, 5), "WEBPXTICK_DT-20130408.zip")
        self.assertEquals(download.get_filename(bad_url, 5), None)
    
    def test_download(self):
        source_url = "https://links.sgx.com/1.0.0/derivatives-historical/2757/WEBPXTICK_DT.zip"
        destination_dir = "."
        filename = "WEBPXTICK_DT-20130409.zip"
        retry_count = 3
        download.download(source_url, destination_dir, filename, retry_count)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_find_index(self):
        mapping = download.get_code_to_date_mapping()
        date_1 = datetime.strptime("20130417", "%Y%m%d").date()
        date_2 = datetime.strptime("20130418", "%Y%m%d").date()
        date_3 = datetime.strptime("20130419", "%Y%m%d").date()
        self.assertEquals(download.find_index(date_1, mapping, True), 881)
        self.assertEquals(download.find_index(date_1, mapping, False), 881)
        self.assertEquals(download.find_index(date_2, mapping, True), 882)
        self.assertEquals(download.find_index(date_2, mapping, False), 881)
        self.assertEquals(download.find_index(date_3, mapping, True), 882)
        self.assertEquals(download.find_index(date_3, mapping, False), 882)