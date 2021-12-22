from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload
from clld.web import datatables
from clld.web.datatables.source import Sources
from clld.web.datatables.base import LinkCol, Col, LinkToMapCol
from clld.db.util import get_distinct_values, icontains
from clld.db.meta import DBSession

from gramfinder import models


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



def includeme(config):
    """register custom datatables"""
    config.register_datatable('sources', Documents)