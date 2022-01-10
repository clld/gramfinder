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
from clld_glottologfamily_plugin.models import HasFamilyMixin

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
    inlg = Column(Unicode)
    npages = Column(Integer)
    types = Column(Unicode)
    maxrank = Column(Integer)
    besttxt = Column(Unicode)


@implementer(interfaces.ILanguage)
class GramfinderLanguage(CustomModelMixin, common.Language, HasFamilyMixin):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
    macroarea = Column(Unicode)
    nsources = Column(Integer) #Ugly, since it's derivable form the DB but I don't know how to make SQL views in this system
    hid = Column(Unicode, unique=True) 
    
class Doctype(Base, common.IdNameDescriptionMixin):
    rank = Column(Integer)
    ndocs = Column(Integer) #Ugly, since it's derivable form the DB but I don't know how to make SQL views in this system

class DocumentDoctype(Base):
    __table_args__ = (UniqueConstraint('document_pk', 'doctype_pk'),)

    document_pk = Column(Integer, ForeignKey('document.pk'), nullable=False)
    doctype_pk = Column(Integer, ForeignKey('doctype.pk'), nullable=False)
    document = relationship(Document, backref='doctype_assocs')
    doctype = relationship(Doctype, backref='document_assocs')


class Page(Base):
    number = Column(Integer)
    label = Column(Unicode)
    text = Column(Unicode)
    terms = Column(TSVECTOR)
    document_pk = Column(Integer, ForeignKey('source.pk'))
    document = relationship(Document, backref='scans')
