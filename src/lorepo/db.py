"""
ORM layer for the DB
"""
import functools
from datetime import datetime

from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Table
from sqlalchemy import create_engine
from sqlalchemy import (
    DateTime,
    Boolean,
    Integer,
    Float,
    String,
    Text,
    ForeignKey,
)

from lorepo.conf import settings

Base = declarative_base()

tag_relationship = Table(
    "assoc_tag_to_item",
    Base.metadata,
    Column("tag_id", Integer, ForeignKey("tag.id"), nullable=False),
    Column("item_id", Integer, ForeignKey("item.id"), nullable=False),
)
dependency_relationship = Table(
    "assoc_deps_to_item",
    Base.metadata,
    Column("item_id", Integer, ForeignKey("item.id"), nullable=False),
    Column("dependency_id", Integer, ForeignKey("item.name"), nullable=False),

)

class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, nullable=False)

    deps = relationship(
            "Item",
            secondary=dependency_relationship,
            primaryjoin=id==dependency_relationship.c.item_id,
            secondaryjoin=id==dependency_relationship.c.dependency_id,
            backref="required_by")
    tags = relationship("Tag", secondary=tag_relationship, backref="items")

    key_id = Column("key_id", Integer, ForeignKey("key.id"))
    key = relationship("Key", backref="items")
    
    name = Column(String, nullable=False, unique=True, index=True)
    image = Column(String)
    desc = Column(Text, nullable=False)
    file = Column(String, nullable=False)
    service = Column(String, default="NAI", nullable=False)

    date_created = Column(DateTime, default=datetime.now(), nullable=False)
    date_updated = Column(DateTime)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "deps": [dep.name for dep in self.deps],
            "tags": [tag.name for tag in self.tags],
            "image": self.image,
            "desc": self.desc,
            "file": self.file,
            "service": self.service,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
        }

class Tag(Base):
    """
    Tags that describe the image content
    """
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, index=True, unique=True, nullable=False)

    date_created = Column(DateTime, default=datetime.now(), nullable=False)
    date_updated = Column(DateTime)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
        }

class Key(Base):
    """
    Primitive permissions model
    """
    __tablename__ = "key"

    id = Column(Integer, primary_key=True, nullable=False)
    token = Column(String, index=True, unique=True, nullable=False)
    active = Column(Boolean, index=True, default=True)

    date_created = Column(DateTime, default=datetime.now(), nullable=False)
    date_updated = Column(DateTime)

    def as_dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "active": self.active,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
        }

def create_db(name="sqlite:///./db.sqlite"):
    engine = create_engine(name)

    Base.metadata.create_all(engine)

    return engine

def drop_db(name="sqlite:///./db.sqlite"):
    engine = create_engine(name)
    Base.metadata.drop_all(engine)
