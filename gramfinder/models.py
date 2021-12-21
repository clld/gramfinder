from datetime import datetime
from elasticsearch_dsl import Document as ESDoc
from elasticsearch_dsl import Date, Integer, Keyword, Text
from elasticsearch_dsl import Integer as IntegerField
from elasticsearch_dsl.connections import connections
from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import TSVECTOR

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.models import common


#-----------------------------------------------------------------------------
# specialized common mapper classes
#-----------------------------------------------------------------------------


@implementer(interfaces.ISource)
class Document(CustomModelMixin, common.Source):
    """Words are units of a particular language, but are still considered part of a
    dictionary, i.e. part of a contribution.
    """
    pk = Column(Integer, ForeignKey('source.pk'), primary_key=True)
    nlangs = Column(Integer)
    langs = Column(Unicode)


class Page(Base):
    number = Column(Integer)
    label = Column(Unicode)
    text = Column(Unicode)
    terms = Column(TSVECTOR)
    document_pk = Column(Integer, ForeignKey('source.pk'))
    document = relationship(Document, backref='scans')


class Grammar(ESDoc):
    text = Text(
        analyzer='snowball',
    )
    doctypes = Keyword()

    #
    # FIXME:
    languages = Keyword()
    numlangs = IntegerField()

    class Index:
        name = 'gramfinder'
        settings = {
            'highlight.max_analyzed_offset': 10000000,
        }


def es_schema(es):
    # create the mappings in elasticsearch
    Grammar.init(using=es)
