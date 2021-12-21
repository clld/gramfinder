from sqlalchemy import func
from clld.db.meta import DBSession
from clld.db.models import common
from clld.web.util.htmllib import HTML

from gramfinder import models
from gramfinder.views import search_col


def source_snippet_html(request=None, context=None, **kw):
    #
    # return ts_headline() for all pages matching a query!
    #
    def fragments(s):
        return HTML.ul(
            *[HTML.li(HTML.literal(ss.replace('<<<', '<span style="background: yellow">').replace('>>>', '</span>'))) for ss in s.split('___')]
        )

    res =  DBSession\
        .query(
        models.Page,
        func.ts_headline(
            'english',
            models.Page.text,
            func.websearch_to_tsquery('english', request.params.get('q')),
            'MaxFragments=10 MaxWords=7, MinWords=3, StartSel=<<<, StopSel=>>>, FragmentDelimiter=___'))\
        .filter(models.Page.document_pk == context.pk)\
        .filter(search_col(models.Page.terms, request.params.get('q')))\
        .all()
    return {
        'pages': [
            (p, fragments(f)) for p, f in res
        ],
    }