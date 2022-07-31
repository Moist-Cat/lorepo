import time
import signal
import glob
import os
from multiprocessing import Process
import unittest
from datetime import datetime

import requests

from lorepo.conf import settings, ENVIRONMENT_VARIABLE
from lorepo.server import app
from lorepo.test import build_test_db

TEST_FILES = settings.MEDIA_DIR
TEST_DIR = settings.TEST_DIR

PORT = 14548
HOST = "localhost"
LIVE_TEST = True # Whether use an active test server (manual) or create one on-the-go (automatic)


def run_test_server():
    var = os.environ.get(ENVIRONMENT_VARIABLE)
    os.environ[ENVIRONMENT_VARIABLE] = "lorepo.conf.dev"
    app.run(port=PORT)

    # clean up
    os.environ[ENVIRONMENT_VARIABLE] = var
    delete_test_data()


def delete_test_data():
    imgs = glob.glob(str(settings.BASE_DIR / "static" / "__debug__") + "/*")
    # we don't want anything funny to happen while removing files
    assert len(imgs) in (0, 20, 21), f"Too many images in the test dir. {len(imgs)}"
    for i in imgs:
        os.remove(i)


class TestServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert settings.DEBUG is True, "You can't test with production settings"
        if not LIVE_TEST:
            cls.server = Process(target=run_test_server)
            cls.server.start()

    @classmethod
    def tearDownClass(cls):
        if not LIVE_TEST:
            s = f"kill -s {signal.SIGINT.value} {cls.server.pid}"
            os.system(s)

    def setUp(self):
        build_test_db()
        self.session = requests.Session()
        self.url = f"http://{HOST}:{PORT}/"
        self.json = {
            "name": "remilia",
            "deps": [],
            "tags": ["character", "touhou"],
            "image": "https://imgur.io/dqwd2",
            "desc": "",
            "file": "https://files.catbox.moe/fwef32",
            "service": "NAI",
            "date_created": str(datetime.now()),
            "date_updated": str(datetime.now()),
        }
    def tearDown(self):
        self.session.close()

    def test_create(self):
        res = self.session.post(self.url, json=self.json)

        self.assertEqual(res.status_code, 200, res.content)

    def test_get(self):
        self.test_create()
        res = self.session.get(self.url)

        self.assertIn("remilia", res.text, res.text)

    def test_detail(self):
        self.test_create()
        res = self.session.get(self.url + "remilia")

        self.assertIn("remilia", res.text, res.text)

    def test_update(self):
        self.test_create()
        res = self.session.post(self.url + "remilia", json={"name": "new_name"})

        self.assertIn("new_name", res.text, res.text)
        self.assertIn("touhou", res.text, res.text)

    def test_create_dependency(self):
        self.test_create()
        self.json["name"] = "sakuya"
        dep = self.json
        res = self.session.post(self.url, json=self.json)
        assert res.ok, res.content
        
        self.json["name"] = "remilia"
        self.json["deps"].append("sakuya")
        res = self.session.post(self.url + "remilia", json=self.json)

        try:
            self.assertEqual("sakuya", res.json()["deps"][0]["name"],res.json())
            self.assertEqual(res.json()["deps"][0]["deps"], [], "Dependency relationship is symetrical")
        except (requests.exceptions.JSONDecodeError, KeyError) as exc:
            raise AssertionError(res.text) from exc

    @unittest.expectedFailure
    def test_duplicate(self):
        self.test_create()
        self.test_create()

    def test_unauthorized_update(self):
        self.test_create()
        self.session.headers["Authorization"] = "Authorized"
        res = self.session.post(self.url + "remilia", json={"name": "new_name"})

        self.assertIn("new_name", res.text, res.text)
        self.assertIn("touhou", res.text, res.text)

def main_suite() -> unittest.TestSuite:
    s = unittest.TestSuite()
    load_from = unittest.defaultTestLoader.loadTestsFromTestCase
    s.addTests(load_from(Test_API))

    return s


def run():
    t = unittest.TextTestRunner()
    t.run(main_suite())

