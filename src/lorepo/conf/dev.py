from lorepo.conf._base import *

# Paths
TEST_DIR = Path(__file__).parent.parent / "test"
MEDIA_DIR = TEST_DIR / "media"

# Config
DEBUG = True
# Database
DATABASES = {
        "default": {
            "engine": f"sqlite:///{TEST_DIR}/test_db.sqlite",
            "config": {"autocommit": True}
        },
}
