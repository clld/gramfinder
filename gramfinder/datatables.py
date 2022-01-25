from sqlalchemy import func, desc, and_
from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.source import Sources
from clld.web.datatables.language import Languages
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.web.util.htmllib import HTML
from clld.db.util import get_distinct_values, icontains
from clld.db.meta import DBSession

from clld_glottologfamily_plugin.models import Family
from clld_glottologfamily_plugin.datatables import MacroareaCol, FamilyLinkCol

from gramfinder import models
from gramfinder import config


class IsoCol(Col):
    def format(self, item):
        if item.hid and len(item.hid) == 3:
            return item.hid

    def order(self):
        return models.GramfinderLanguage.hid

    def search(self, qs):
        iso_like = models.GramfinderLanguage.hid.op('~')('^[a-z]{3}$')
        return and_(models.GramfinderLanguage.hid.contains(qs.lower()), iso_like)


class DoctypeCol(Col):
    def order(self):
        return models.Document.maxrank

    def search(self, qs):
        return icontains(models.Document.types, qs)

    def format(self, item):
        return HTML.ul(*[HTML.li(t) for t in item.types.split()], class_='unstyled')


class InlgCol(Col):
    def order(self):
        return models.Document.inlg_pk

    def search(self, qs):
        return models.Inlg.id == qs

    def format(self, item):
        return config.INLGS.get(item.inlg.id, item.inlg.id)


class Documents(Sources):
    def base_query(self, query):
        return query.join(models.Document.inlg)\
            .outerjoin(models.DocumentDoctype).outerjoin(models.Doctype).distinct()\
            .options(joinedload(models.Document.inlg))

    def col_defs(self):
        return [
            LinkCol(self, 'src'),
            Col(self, 'description', sTitle='title'),
            InlgCol(self, 'inlg', choices=config.inlgs().items()),
            Col(self, 'npages', model_col=models.Document.npages),
            Col(self, 'nlangs', model_col=models.Document.nlangs),
            DoctypeCol(
                self,
                'doctype',
                model_col=models.Document.types,
                choices=[dt.name for dt in DBSession.query(models.Doctype).order_by(desc(models.Doctype.rank))]),
        ]


class LanguageIdCol(LinkCol):
    def get_attrs(self, item):
        return dict(label=item.id)


class GramfinderLanguages(Languages):
    __constraints__ = [Family]

    def base_query(self, query):
        if self.family:
            return query.join(Family).filter(models.GramfinderLanguage.family == self.family).options(joinedload(models.GramfinderLanguage.family))
        return query.outerjoin(Family).options(joinedload(models.GramfinderLanguage.family))

    def col_defs(self):
        return [
            LanguageIdCol(self, 'id'),
            LinkCol(self, 'name'),
            IsoCol(self, 'ISO'),
            LinkToMapCol(self, 'm'),
            Col(self,
                'latitude',
                sDescription='<small>The geographic latitude</small>'),
            Col(self,
                'longitude',
                sDescription='<small>The geographic longitude</small>'),
            MacroareaCol(self, 'macroarea', models.GramfinderLanguage),
            FamilyLinkCol(self, 'family', models.GramfinderLanguage),
            Col(self, 'Sources', model_col=models.GramfinderLanguage.nsources),
        ]



def includeme(config):
    """register custom datatables"""
    config.register_datatable('sources', Documents)
    config.register_datatable('languages', GramfinderLanguages)
