import math
import time
import collections

from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import joinedload
from clld.db.meta import DBSession
from clld.db.models import common
from matplotlib.cm import viridis
from matplotlib.colors import to_hex

from gramfinder import models
from gramfinder.maps import SearchMap
from gramfinder import config


def vir(n):
    return to_hex(viridis(float(n)))


def search(ctx, req):
    doctypes = DBSession.query(models.Doctype).order_by(desc(models.Doctype.rank)).all()
    inlgs = {r.id: r for r in DBSession.query(models.Inlg)}
    ndocs = DBSession.query(models.Document).count()
    cutoff = 400 if ndocs > 1000 else 10
    selected_doctypes = {t.partition('-')[2] for t in req.params if t.startswith('dt-')} \
                        or ["grammar", "grammar_sketch"]
    tmpl = {
        'hits': [],
        'q': {},
        'inlgs': sorted([(r.id, r.description, r.ndocs) for r in inlgs.values() if r.ndocs > cutoff], key=lambda i: -i[2]) + [('any', 'All', ndocs)],
        'inlg_map': inlgs,
        'doctypes': [(dt, dt.id in selected_doctypes) for dt in doctypes],
    }

    s = time.time()
    print('searching ...')
    q = {t.partition('-')[2]: s for t, s in req.params.items() if t.startswith('query-') and s.strip()}
    if not q:
        return tmpl

    by_lg = collections.defaultdict(list)

    def qinlgtyp(q, inlg):
        if inlg == 'any':
            return config.tsearch(models.Page.terms, q, 'simple')
        return and_(models.Document.inlg_pk == inlgs[inlg].pk, config.tsearch(models.Page.terms, q, inlg))

    dt_id2pk = {dt.id: dt.pk for dt in doctypes}
    selected_doctypes = set(dt_id2pk[dt] for dt in selected_doctypes)
    res =  DBSession\
        .query(models.Document, func.count(models.Page.pk))\
        .join(models.Page) \
        .join(models.DocumentDoctype)\
        .filter(models.DocumentDoctype.doctype_pk.in_(selected_doctypes))\
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

    langs = {l.id: l for l in DBSession.query(common.Language)\
        .options(joinedload(models.GramfinderLanguage.family))\
        .filter(common.Language.id.in_(list(by_lg)))}
    #print(len(res))

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
    })
    print('... done: {}'.format(time.time() - s))
    return tmpl