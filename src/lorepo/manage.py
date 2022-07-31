import os
from lorepo.db import create_db
from lorepo.conf import settings
import sys

def get_command(command: list=sys.argv[1]):
    """Macros to maange the db"""
    if command == "shell":
        import lorepo.test.shell

    elif command == "migrate":
        create_db(settings.DATABASES["default"]["engine"])

    elif command == "test":
        os.system("pytest src/lorepo")
    elif command == "runserver":
        from lorepo.server import runserver
        runserver()
    elif command == "livetest":
        from lorepo.test.test_ft import run_test_server
        run_test_server()


if __name__ == "__main__":
    get_command()
