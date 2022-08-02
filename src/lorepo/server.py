import os
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from flask import Flask, request, jsonify
from flask.app import BadRequest

from lorepo.conf import settings
from lorepo.db import Item, Tag, Key
from lorepo.log import logged

PAGE_SIZE = 10

def make_app():

    app = Flask(__name__)

    db = settings.DATABASES["default"]
    engine = db["engine"]
    config = db["config"]

    engine = create_engine(engine)
    Session = sessionmaker(bind=engine, **config)
    session = Session()

    # we can't use session
    app.objects = session

    @app.errorhandler(BadRequest)
    def error_message(ex):
        current_app.logger.error(f"{ex.args}")
        return jsonify(status="Bad Request", message=ex.args), HTTPStatus.BAD_REQUEST

    return app

app = make_app()

def get_args(req, args, sep=","):
    res = {}
    for arg in args:
        if arg in req.args and req.args[arg]:
            val = req.args[arg]
            if val.isdigit():
                val = int(val)
            elif "," in val:
                val = val.split(sep)
        else:
            val = None
        res[arg] = val
    return res

@app.route("/docs")
def docs():
    return {
        "urls": {
            "/": {
                "methods": ["GET", "POST"],
                "scheme": {
                    "id": "number",
                    "name": "string",
                    "deps": "[item_id1, item_id2, ..., item_idn]",
                    "tags": "[string_1, string_2, ..., string_n]",
                    "image": "string",
                    "desc": "string",
                    "file": "string",
                    "service": "string",
                    "date_created": "date string, ISO format",
                    "date_updated": "date string, ISO format",
                }
            },
            "/<int:id>": {
                "methods": ["GET", "POST"],
                "scheme": {
                    "id": "number",
                    "name": "string",
                    "deps": "[item_id1, item_id2, ..., item_idn]",
                    "tags": "[string_1, string_2, ..., string_n]",
                    "image": "string",
                    "desc": "string",
                    "file": "string",
                    "service": "string",
                    "date_created": "date string, ISO format",
                    "date_updated": "date string, ISO format",
                }
            }
        }
    }

@app.route("/", methods=["GET", "POST"])
def catalog():
    """Lists all packages. Supports filtering by tag"""
    if request.method == "POST":
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
        elif "LOREPO_NO_AUTH" in os.environ:
            token = "redarmy"
        else:
            return ("{'errors': 'Authorization token missing'}", 403)
        data = request.json

        deps = [app.objects.query(Item).get(dep) for dep in data.pop("deps", [])]
        _tags = data.pop("tags", [])
        tags = []
        for name in _tags:
            try:
                tag = app.objects.query(Tag).filter(Tag.name == name).one()
            except sqlalchemy.exc.NoResultFound:
                tag = Tag(name=name)
            tags.append(tag)
        if "date_created" in data:
            del data["date_created"]
        data["date_updated"] = datetime.now()

        item = Item(**data)
        item.deps = deps
        item.tags = tags
        
        try:
            key = app.objects.query(Key).filter(Key.token == token).one()
        except sqlalchemy.exc.NoResultFound:
            key = Key(token=token)
        except sqlalchemy.exc.IntegrityError as exc:
            app.logger.info(exc)
            return ("{'errors': '%s'}" % str(exc).split("\n")[1][25:], 400)
        key.items.append(item)

        app.objects.add(item)

        return jsonify(item.as_dict())

    args = {"page", "tags", "name"}
    args = get_args(request, args)

    tags = args["tags"] or []
    page = args["page"] or 0
    name = args["name"]
    size = PAGE_SIZE
    start = PAGE_SIZE * page

    query = app.objects.query(Item)

    if tags:
        query = query.select_from(Tag).filter(Tag.name.like(f"%{tags.pop()}%")).items
        for tag in tags:
            query = query.intersect(app.objects.filter(Tag.name.like(f"%{tag}%"))).items
    if name:
        query = query.filter(Item.name.like(f"%{name}%"))
    res = query.offset(start).limit(size).all()
    return jsonify([item.as_dict() for item in res])

@app.route("/<name>", methods=["POST", "GET"])
def item_detail(name):
    if "Authorization" in request.headers:
        token = request.headers["Authorization"]
    elif "LOREPO_NO_AUTH" in os.environ:
        token = "redarmy"
    else:
        return ('{"errors": "Authorization token missing"}', 403)

    try:
        key = app.objects.query(Key).filter(Key.token == token).one()
    except sqlalchemy.exc.NoResultFound:
        key = Key(token=token)
    except sqlalchemy.exc.IntegrityError as exc:
        app.logger.info(exc)
        return ('{"errors": "%s"}' % str(exc).split("\n")[1][25:], 400)

    try:
        item = app.objects.query(Item).filter(Item.name == name).one()
    except sqlalchemy.exc.NoResultFound:
        return ("{'errors': 'Not found'}", 404)

    if key != item.key:
        return ('{"errors": "Unauthorized"}', 403)

    if request.method == "POST":
        data = request.json
        if "deps" in data:
            _deps = data.pop("deps")
            deps = []
            if any(_deps):
                for dep in _deps:
                    try:
                        deps.append(app.objects.query(Item).filter(Item.name == dep).one())
                    except sqlalchemy.exc.NoResultFound:
                        app.logger.warning("The dependency '%s' from %s doesn't exist.", dep, item.name)
            app.logger.info(deps)
            item.deps = deps
        if "tags" in data:
            _tags = data.pop("tags", [])
            tags = []
            if any(_tags):
                for name in _tags:
                    try:
                        tag = app.objects.query(Tag).filter(Tag.name == name).one()
                    except sqlalchemy.exc.NoResultFound:
                        tag = Tag(name=name)
                    tags.append(tag)
            item.tags = tags
        if "date_created" in data:
            del data["date_created"]
        data["date_updated"] = datetime.now()
        for col in data:
            setattr(item, col, data[col])
    return jsonify(item.as_dict())

def runserver():
    app.run(port=5050)
