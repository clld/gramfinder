import itertools
import collections

from sqlalchemy import func, or_
from clld.db.meta import DBSession
from clld.db.models import common
from clld.web.util.htmllib import HTML
from clld.web.util.helpers import get_referents
import attr

from gramfinder import models
from gramfinder import config


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

    def parse(self, f):
        return [
            ss.replace(
                self.StartSel, '<span style="background: yellow">').replace(
                self.StopSel, '</span>')
            for ss in f.split(self.FragmentDelimiter) if self.StartSel in ss]



def iter_fragments(document, req, q=None, inlgs=None, options=None):
    options = options or FragmentOptions()

    for inlg in inlgs or [document.inlg, 'any']:
        q = q or req.params.get('query-{}'.format(inlg))
        if not q:
            continue
        for pid, fs in itertools.groupby(
                DBSession\
                .query(
                    models.Page,
                    func.ts_headline(
                        config.stemmer(inlg),
                        models.Page.text,
                        func.websearch_to_tsquery(config.stemmer(inlg), q),
                        str(options))) \
                .filter(models.Page.document_pk == document.pk) \
                .filter(config.tsearch(models.Page.terms, q, inlg))\
                .order_by(models.Page.document_pk, models.Page.number),
                lambda i: i[0].number,
            ):
            p, frags = None, []
            for p, f in fs:
                for ff in options.parse(f):
                    if ff not in frags:
                        frags.append(ff)
            yield p, frags


def language_detail_html(context=None, request=None, **kw):
    hits = []
    for k, v in request.params.items():
        if k.startswith('query-') and v.strip():
            doc = models.Document.get(int(k.partition('-')[2]))
            hits.append((
                doc,
                sorted(
                    list(iter_fragments(
                        doc,
                        request,
                        q=v.strip(),
                        inlgs=[doc.inlg or 'any'],
                        options=FragmentOptions(MaxFragments=100, MaxWords=20, MinWords=5),
                    )),
                    key=lambda i: i[0].number)
            ))
    return {'hits': hits}


def source_detail_html(context=None, request=None, **kw):
    return {'referents': get_referents(context)}


def source_snippet_html(request=None, context=None, **kw):
    return {
        'pages': [
            (p, HTML.ul(*[HTML.li(HTML.literal(f)) for f in fs])) for p, fs in iter_fragments(context, request)]}
