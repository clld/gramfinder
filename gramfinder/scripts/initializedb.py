import re
import pathlib
import itertools
import collections

import tqdm
from pycldf import Sources, Source
from clldutils.misc import nfilter
from clldutils.color import qualitative_colors
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clld.db import fts
from pybtex.database import parse_string
from unidecode import unidecode
from pyglottolog.references import BibFile
from pyglottolog import Glottolog

import gramfinder
from gramfinder import models
from sqlalchemy import func, Index

DATA = pathlib.Path(__file__).parent.parent.parent.parent
INDEX = 'gramfinder'

#
# FIXME: split pages at
PAGENO_PATTERN = re.compile('\f(?P<no>[^\s]*)')
#


def iter_pages(text):
    label = None
    for i, t in enumerate(PAGENO_PATTERN.split(text)):
        if i % 2 == 0:
            yield t, label
        else:
            label = t or None


def tsvector(text, lg):  # pragma: no cover
    lang = 'english'
    if '[tur]' in lg:
        lang = 'turkish'
    return func.to_tsvector(lang, text)


def get_text(p):
    try:
       res = p.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            res = p.read_text(encoding='cp1252')
        except UnicodeDecodeError:
            res = p.read_text(encoding='latin1')
    res = unidecode(res)
    return res.replace("\x00", "")


def main(args):
    assert DATA.exists(), str(DATA)

    fts.index('fts_index', models.Page.terms, DBSession.bind)

    data = Data()
    data.add(
        common.Dataset,
        gramfinder.__name__,
        id=gramfinder.__name__,
        domain='',

        publisher_name="Max Planck Institute for the Science of Human History",
        publisher_place="Jena",
        publisher_url="http://www.shh.mpg.de",
        license="http://creativecommons.org/licenses/by/4.0/",
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},

    )

    ndocs = 0
    gl = Glottolog(args.glottolog)
    langs_by_id = gl.languoids_by_code()
    bibdata = BibFile(DATA.joinpath('hh10000.bib'))
    for e in tqdm.tqdm(bibdata.iterentries()):
        if 'besttxt' in e.fields:
            ndocs += 1
            #if ndocs > 100:
            #    break
            #print(e.key)
            besttxt = DATA.joinpath('more', *e.fields['besttxt'].split('\\'))
            assert besttxt.exists(), str(besttxt)

            rec = bibtex.Record(e.type, e.key, **e.fields)
            src = data.add(models.Document, e.key, _obj=bibtex2source(rec, cls=models.Document))

            i = 0
            for i, (p, label) in enumerate(iter_pages(get_text(besttxt)), start=1):
                DBSession.add(models.Page(
                    number=i,
                    document=src,
                    label=label,
                    text=p,
                    terms=tsvector(p, e.fields.get('inlg') or '')))
            print('{}: {} pages'.format(e.key, i))

            langs, _ = e.languoids(langs_by_id)
            src.nlangs = len(langs)
            src.langs = ' '.join({l.id for l in langs})
            for l in langs:
                lg = data['Language'].get(l.id)
                if not lg:
                    lg = data.add(common.Language, l.id, id=l.id, name=l.name, latitude=l.latitude, longitude=l.longitude)


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
    langs = dict(DBSession.query(common.Language.id, common.Language.pk))
    for doc in DBSession.query(models.Document):
        for lid in doc.langs.split():
            DBSession.add(common.LanguageSource(source_pk=doc.pk, language_pk=langs[lid]))
