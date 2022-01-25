import collections

from sqlalchemy import func
from clld.db.meta import DBSession
from unidecode import unidecode

from gramfinder import models

INLGS = collections.OrderedDict([
    # isocode: (name, stemmer)
    ('eng', 'english'),
    ('fra', 'french'),
    ('deu', 'german'),
    ('spa', 'spanish'),
    ('rus', 'russian'),
    ('por', "portuguese"),
    ('ind', 'indonesian'),
    ('cmn', 'chinese'),
    ('nld', 'dutch'),
    ('swe', 'swedish'),
    ('arb', 'arabic'),
    ('dan', 'danish'),
    ('ita', 'italian'),
    #'pes': '',  # No Persian stemmer available
    ('tur', 'turkish'),
])
STEM = {'chinese': 'simple'}  # No Chinese stemmer available


def inlgs():
    return collections.OrderedDict([
        (k, v) for k, v in INLGS.items()
        if k in set(r[0] for r in DBSession.query(models.Inlg.id).distinct())])


def stemmer(lg):
    for code, name in INLGS.items():
        if code == lg:
            break
    else:
        name = 'simple'
    return STEM.get(name, name)


def tsearch(col, qs, inlg):  # pragma: no cover
    return col.op('@@')(func.websearch_to_tsquery(stemmer(inlg), unidecode(qs)))
