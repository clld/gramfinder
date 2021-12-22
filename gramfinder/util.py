from sqlalchemy import func
from clld.db.meta import DBSession
from clld.db.models import common
from clld.web.util.htmllib import HTML
import attr

from gramfinder import models
from gramfinder.views import search_col


@attr.s
class FragmentOptions:
    """
    https://www.postgresql.org/docs/11/textsearch-controls.html#TEXTSEARCH-HEADLINE
    """
    MaxWords = attr.ib(default=10)
    MinWords = attr.ib(default=3)
    ShortWord = attr.ib(default=3)
    MaxFragments = attr.ib(default=10)
    StartSel = attr.ib(default='<<<')
    StopSel = attr.ib(default='>>>')
    FragmentDelimiter = attr.ib(default='___')

    def __str__(self):
        return ', '.join(['{}={}'.format(k, v) for k, v in attr.asdict(self).items()])

    def format(self, f):
        return HTML.ul(
            *[HTML.li(HTML.literal(ss.replace(self.StartSel, '<span style="background: yellow">')
                                   .replace(self.StopSel, '</span>')))
              for ss in f.split(self.FragmentDelimiter)]
        )


def iter_fragments(document, req):
    options = FragmentOptions()
    for p, f in DBSession \
            .query(
            models.Page,
            func.ts_headline(
                'english',
                models.Page.text,
                func.websearch_to_tsquery('english', req.params.get('q')),
                str(options))) \
            .filter(models.Page.document_pk == document.pk) \
            .filter(search_col(models.Page.terms, req.params.get('q'))):
        yield p, options.format(f)


def source_snippet_html(request=None, context=None, **kw):
    return {'pages': list(iter_fragments(context, request))}
