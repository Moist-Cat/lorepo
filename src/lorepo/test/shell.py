import os
import sys
import traceback

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from lorepo.conf import settings
from lorepo.db import *
from lorepo.server import *

ENGINE = settings.DATABASES["default"]["engine"]
config = settings.DATABASES["default"]["config"]

engine = create_engine(ENGINE)
Session = sessionmaker(bind=engine, **config)
session = Session()

version = "0.1.0"

print("DB client interactive shell. Ctrl-C to clear, Ctrl-D to exit.")
print(f"{version=}")
while True:
    print(">>> ", end="")
    try:
        string = input()
        if "=" not in string:
            print(eval(string))
        exec(string)
    except KeyboardInterrupt:
        os.system("clear")
    except EOFError:
        print("\nbye bye")
        break
    except Exception as e:
        cls, exc, tb = sys.exc_info()
        print("Traceback (most recent call last):")
        traceback.print_tb(tb)
        print(f"{cls.__name__}:", exc)
