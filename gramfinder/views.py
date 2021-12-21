import math
import collections

from sqlalchemy import func
from unidecode import unidecode
from clld.db import fts
from clld.db.meta import DBSession
from clld.db.models import common
from matplotlib.cm import viridis
from matplotlib.colors import to_hex
from clldutils.svg import icon, data_url

from gramfinder import models
from gramfinder.maps import SearchMap


def search_col(col, qs):  # pragma: no cover
    #qs = qs.replace(' OR ', ' | ')
    #qs = qs.replace(' AND ', ' & ')
    query = func.websearch_to_tsquery('english', unidecode(qs))
    return col.op('@@')(query)


def search(ctx, req):
    q = req.params.get('q')
    if not q:
        return {'hits': [], 'q': ''}
    by_lg = collections.defaultdict(list)
    res =  DBSession\
        .query(models.Document, func.count(models.Page.pk))\
        .join(models.Page)\
        .filter(search_col(models.Page.terms, q))\
        .group_by(models.Document.pk, common.Source.pk)\
        .all()
    for doc, c in res:
        for lid in doc.langs.split():
            by_lg[lid].append((doc, c))

    occs = [sum(c for _, c in l) for l in by_lg.values()]
    occs = {c: math.log(c) for c in occs}
    min_occs = min(occs.values())
    max_occs = max(occs.values())
    colors = {o: to_hex(viridis(float(lo - min_occs) / (max_occs - min_occs))) for o, lo in occs.items()}

    langs = {l.id: l for l in DBSession.query(common.Language).filter(common.Language.id.in_(list(by_lg)))}
    #print(len(res))
    return {
        'map': SearchMap(
            ([langs[lid] for lid in by_lg], {lid: colors[sum(c for _, c in hits)] for lid, hits in by_lg.items()}),
            req),
        'hits': res,
        'q': q,
        'by_lg': by_lg,
        'langs': langs,
    }
