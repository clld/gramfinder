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


class Inlg(Base, common.IdNameDescriptionMixin):
    ndocs = Column(Integer)


@implementer(interfaces.ISource)
class Document(CustomModelMixin, common.Source):
    pk = Column(Integer, ForeignKey('source.pk'), primary_key=True)
    langs = Column(Unicode)
    nlangs = Column(Integer)
    inlg_pk = Column(Integer, ForeignKey('inlg.pk'), index=True)
    inlg = relationship(Inlg)
    npages = Column(Integer)
    besttxt = Column(Unicode)
    fn = Column(Unicode)
    types = Column(Unicode)
    maxrank = Column(Integer)

    @property
    def maxtype(self):
        for dta in self.doctype_assocs:
            if dta.doctype.rank == self.maxrank:
                return dta.doctype


@implementer(interfaces.ILanguage)
class GramfinderLanguage(CustomModelMixin, common.Language, HasFamilyMixin):
    pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
    macroarea = Column(Unicode)
    hid = Column(Unicode, unique=True)
    nsources = Column(Integer)

    @property
    def sorted_sources(self):
        return sorted(self.sources, key=lambda src: (-src.maxrank, -src.npages))


class Doctype(Base, common.IdNameDescriptionMixin):
    rank = Column(Integer)
    ndocs = Column(Integer)


class DocumentDoctype(Base):
    __table_args__ = (UniqueConstraint('document_pk', 'doctype_pk'),)

    document_pk = Column(Integer, ForeignKey('document.pk'), nullable=False)
    doctype_pk = Column(Integer, ForeignKey('doctype.pk'), nullable=False, index=True)
    document = relationship(Document, backref='doctype_assocs')
    doctype = relationship(Doctype, backref='document_assocs')


class Page(Base):
    number = Column(Integer)
    label = Column(Unicode)
    text = Column(Unicode)
    terms = Column(TSVECTOR)
    document_pk = Column(Integer, ForeignKey('document.pk'), index=True)
    document = relationship(Document, backref='scans')
