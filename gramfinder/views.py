import math
import time
import collections

from sqlalchemy import func, or_, and_
from unidecode import unidecode
from clld.db import fts
from clld.db.meta import DBSession
from clld.db.models import common
from matplotlib.cm import viridis
from matplotlib.colors import to_hex
from clldutils.svg import icon, data_url
from clld.db.util import icontains

from gramfinder import models
from gramfinder.maps import SearchMap

def search_col(col, qs):  # pragma: no cover
    #qs = qs.replace(' OR ', ' | ')
    #qs = qs.replace(' AND ', ' & ')
    query = func.websearch_to_tsquery('english', unidecode(qs))
    return col.op('@@')(query)


def vir(n):
    return to_hex(viridis(float(n)))


def search(ctx, req, default_doctypes = set(["grammar", "grammar_sketch"]), inlgs = [("English", "eng"), ("French", "fra"), ("German", "deu"), ("Spanish", "spa"), ("Russian", "rus"), ("Portuguese", "por"), ("Indonesian", "ind"), ("Chinese", "cmn"), ("Dutch", "nld"), ("Swedish", "swe")]):
    doctypes = DBSession.query(models.Doctype).order_by(models.Doctype.rank.desc())

    s = time.time()
    print('searching ...')
    #q = req.params.get('q')
    #print(req.params) #, dts)
    qs = {x.replace("q_", ""): xv for (x, xv) in req.params.items() if x.startswith("q_") and xv.strip()}
    qlgs = {x.replace("s_", ""): xv for (x, xv) in req.params.items() if x.startswith("s_")}
    if not qs:
        return {'hits': [], 'qs': {}, 'qlgs': qlgs, 'doctypes': [(dt.id, dt.ndocs, dt.id in default_doctypes) for dt in doctypes], 'inlgs': inlgs}

    by_lg = collections.defaultdict(list)
    selected_doctypes = set(dt.id for dt in doctypes if req.params.get(dt.id) == "on")
    qinlgtyp = lambda q, inlg, doctypes = selected_doctypes: and_(models.Document.types.in_(selected_doctypes), inlg == "ANY" or models.Document.inlg == inlg, search_col(models.Page.terms, q))
    res =  DBSession\
        .query(models.Document, func.count(models.Page.pk))\
        .join(models.Page)\
        .filter(or_(qinlgtyp(q, qlgs[n]) for (n, q) in qs.items()))\
        .group_by(models.Document.pk, common.Source.pk)\
        .all()
    for doc, c in res:
        for lid in doc.langs.split():
            by_lg[lid].append((doc, c))

    occs = [sum(c for _, c in l) for l in by_lg.values()]
    min_occs, max_occs = min(occs), max(occs)
    occs = {c: math.log(c) for c in occs}
    min_log_occs = min(occs.values())
    max_log_occs = max(occs.values())
    colors = {
        o: vir(float(lo - min_log_occs) / (max_log_occs - min_log_occs))
        for o, lo in occs.items()}

    langs = {l.id: l for l in DBSession.query(common.Language).filter(common.Language.id.in_(list(by_lg)))}
    #print(len(res))
    res = {
        'map': SearchMap(
            (
                [langs[lid] for lid in by_lg],
                {lid: colors[sum(c for _, c in hits)] for lid, hits in by_lg.items()},
                [(min_occs, vir(0)), (None, vir(0.25)), (None, vir(0.5)), (None, vir(0.75)), (max_occs, vir(1))],
            ),
            req),
        'hits': res,
        'qs': qs,
        'qlgs': qlgs,
        'by_lg': by_lg,
        'langs': langs,
        'doctypes': [(dt.id, dt.ndocs, dt.id in selected_doctypes) for dt in doctypes],
        'inlgs': inlgs
    }
    print('... done: {}'.format(time.time() - s))
    return res
