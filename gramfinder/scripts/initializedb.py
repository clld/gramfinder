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

STEM = {
    'arb': 'arabic',
    'dan': 'danish',
    'nld': 'dutch',
    'fra': 'french',
    'deu': 'german',
    'ind': 'indonesian',
    'ita': 'italian',
    #'pes': '',  # No Persian stemmer available
    'rus': 'russian',
    'spa': 'spanish',
    'swe': 'swedish',
    'tur': 'turkish',
}


def tsvector(text, lg):  # pragma: no cover
    for code, name in STEM.items():
        if '[{}]'.format(code) in lg:
            break
    else:
        name = 'english'
    return func.to_tsvector(name, text)


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

        publisher_name="Max Planck Institute for Evolutionary Anthropology",
        publisher_place="Leipzig",
        publisher_url="http://www.eva.mpg.de",
        license="http://creativecommons.org/licenses/by/4.0/",
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},

    )

    ndocs = 0
    gl = Glottolog(args.glottolog)
    dt_by_id = {}
    for ht in gl.hhtypes:
        dt_by_id[ht.id] = ht
        data.add(
            models.Doctype, ht.id, id=ht.id, name=ht.name, description=ht.description, rank=ht.rank)
    langs_by_id = gl.languoids_by_code()

    for e in tqdm.tqdm(itertools.filterfalse(
            lambda i: not i.fields.get('besttxt'),
            BibFile(DATA.joinpath('hh10000.bib')).iterentries())):
        ndocs += 1
        if ndocs > 100:
            break
        #print(e.key)
        besttxt = DATA.joinpath('more', *e.fields['besttxt'].split('\\'))
        assert besttxt.exists(), str(besttxt)

        rec = bibtex.Record(e.type, e.key, **e.fields)
        src = data.add(models.Document, e.key, _obj=bibtex2source(rec, cls=models.Document))
        src.inlg = e.fields.get('inlg')

        i = 0
        for i, t in enumerate(get_text(besttxt).split('\f'), start=1):
            DBSession.add(models.Page(
                number=i,
                document=src,
                text=t,
                terms=tsvector(t, e.fields.get('inlg') or '')))
        src.npages = i
        #print('{}: {} pages'.format(e.key, i))

        langs, _ = e.languoids(langs_by_id)
        src.nlangs = len(langs)
        src.langs = ' '.join({l.id for l in langs})
        for l in langs:
            if l.id not in data['Language']:
                data.add(
                    common.Language, l.id,
                    id=l.id, name=l.name, latitude=l.latitude, longitude=l.longitude)

        types = []
        for ht in e.doctypes(dt_by_id)[0]:
            types.append((ht.name, ht.rank))
            DBSession.add(models.DocumentDoctype(document=src, doctype=data['Doctype'][ht.id]))
        src.types = ';'.join([i[0] for i in types])
        src.maxrank = max([i[1] for i in types])


def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """
    langs = dict(DBSession.query(common.Language.id, common.Language.pk))
    for doc in DBSession.query(models.Document):
        for lid in doc.langs.split():
            DBSession.add(common.LanguageSource(source_pk=doc.pk, language_pk=langs[lid]))
