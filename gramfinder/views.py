import math
import time
import itertools
import collections

from sqlalchemy import func, or_, and_, desc
from unidecode import unidecode
from clld.db import fts
from clld.db.meta import DBSession
from clld.db.models import common
from matplotlib.cm import viridis
from matplotlib.colors import to_hex
from clldutils.svg import icon, data_url
from clld.db.util import icontains
from clld.web.util.multiselect import MultiSelect

from gramfinder import models
from gramfinder.maps import SearchMap
from gramfinder import config



def vir(n):
    return to_hex(viridis(float(n)))


def search(ctx, req):
    doctypes = DBSession.query(models.Doctype).order_by(desc(models.Doctype.rank))
    inlgs = [(v.capitalize(), k) for k, v in config.inlgs().items()]
    selected_doctypes = req.params.getall('doctypes') or ["grammar", "grammar_sketch"]

    tmpl = {
        'hits': [],
        'q': {},
        'inlgs': inlgs,
        'ms': MultiSelect(
            req,
            'doctypes',
            'doctypes',
            collection=doctypes,
            selected=[dt for dt in doctypes if dt.id in (selected_doctypes)])
    }

    s = time.time()
    print('searching ...')
    q = {t.partition('-')[2]: s for t, s in req.params.items() if t.startswith('query-') and s.strip()}
    if not q:
        return tmpl

    by_lg = collections.defaultdict(list)

    def qinlgtyp(q, inlg):
        if inlg == 'any':
            return config.tsearch(models.Page.terms, q, models.Document.inlg)
        return and_(models.Document.inlg == inlg, config.tsearch(models.Page.terms, q, inlg))

    res =  DBSession\
        .query(models.Document, func.count(models.Page.pk))\
        .join(models.Page) \
        .join(models.DocumentDoctype)\
        .join(models.Doctype)\
        .filter(models.Doctype.id.in_(selected_doctypes))\
        .filter(or_(*[qinlgtyp(term, inlg) for inlg, term in q.items()]))\
        .group_by(models.Document.pk, common.Source.pk)\
        .all()
    for doc, c in res:
        for lid in doc.langs.split():
            by_lg[lid].append((doc, c))

    occs = [sum(c for _, c in l) for l in by_lg.values()]
    if not occs:
        return tmpl

    min_occs, max_occs = min(occs), max(occs)
    occs = {c: math.log(c) for c in occs}
    min_log_occs = min(occs.values())
    max_log_occs = max(occs.values())
    colors = {
        o: vir(float(lo - min_log_occs) / (max_log_occs - min_log_occs) if max_log_occs > min_log_occs else 0)
        for o, lo in occs.items()}

    langs = {l.id: l for l in DBSession.query(common.Language).filter(common.Language.id.in_(list(by_lg)))}
    #print(len(res))

    #class DoctypeMultiSelect(MultiSelect):

    tmpl.update({
        'map': SearchMap(
            (
                [langs[lid] for lid in by_lg],
                {lid: colors[sum(c for _, c in hits)] for lid, hits in by_lg.items()},
                [(min_occs, vir(0)), (None, vir(0.25)), (None, vir(0.5)), (None, vir(0.75)), (max_occs, vir(1))],
            ),
            req),
        'hits': res,
        'q': q,
        'by_lg': by_lg,
        'langs': langs,
        'inlgs': inlgs,
    })
    print('... done: {}'.format(time.time() - s))
    return tmpl