from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.source import Sources
from clld.web.datatables.language import Languages
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.db.util import get_distinct_values, icontains
from clld.db.meta import DBSession

from clld_glottologfamily_plugin.models import Family
from clld_glottologfamily_plugin.datatables import MacroareaCol, FamilyLinkCol

from gramfinder import models

class IsoCol(Col):
    def format(self, item):
        if item.hid and len(item.hid) == 3:
            return item.hid

    def order(self):
        return Languoid.hid

    def search(self, qs):
        iso_like = Languoid.hid.op('~')('^[a-z]{3}$')
        return and_(Languoid.hid.contains(qs.lower()), iso_like)

class DoctypeCol(Col):
    def order(self):
        return models.Document.maxrank

    def search(self, qs):
        return icontains(models.Document.types, qs)


class Documents(Sources):
    def base_query(self, query):
        return query.outerjoin(models.DocumentDoctype).outerjoin(models.Doctype).distinct()

    def col_defs(self):
        return [
            LinkCol(self, 'src'),
            Col(self, 'inlg', model_col=models.Document.inlg, choices=get_distinct_values(models.Document.inlg)),
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
