from lorepo.conf._base import *

# Config
DEBUG = False

# Database
DATABASES = {
        "default": {
            "engine": f"sqlite:///{BASE_DIR}/db.sqlite",
            "config": {"autocommit": True}
        }
}
