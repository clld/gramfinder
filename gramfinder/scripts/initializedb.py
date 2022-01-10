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

DATA = pathlib.Path(__file__).parent.parent.parent.parent.joinpath("dbs\\") if pathlib.Path(__file__).parent.parent.parent.parent.joinpath("dbs").exists() else pathlib.Path(__file__).parent.parent.parent.parent.joinpath("more")
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

#def tsvector(text, lg):  # pragma: no cover
#    for code, name in STEM.items():
#        if '[{}]'.format(code) in lg:
#            break
#    else:
#        name = 'english'
#    return func.to_tsvector(name, text)


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

    #print("gramfinder name", gramfinder.__name__)
    gl = Glottolog(args.glottolog or "..\\glottolog\\")
    bib = gl.bibfiles['hh']    
    #bib = BibFile(DATA.joinpath('hh10000.bib'))
    dt_by_id = {ht.id: ht for ht in gl.hhtypes}
    htndocs = {}
    for e in tqdm.tqdm(itertools.filterfalse(
            lambda i: not i.fields.get('besttxt'), bib.iterentries())):
        for ht in e.doctypes(dt_by_id)[0]:
            htndocs[ht.id] = htndocs.get(ht.id, 0) + 1
 
    for ht in gl.hhtypes:
        if htndocs.get(ht.id, 0) > 0:
            data.add(
                models.Doctype, ht.id, id=ht.id, name=ht.name, description=ht.description, rank=ht.rank, ndocs = htndocs[ht.id])

    
    langs_by_id = gl.languoids_by_code()

    ndocs = 0
    for e in tqdm.tqdm(itertools.filterfalse(
            lambda i: not i.fields.get('besttxt'), bib.iterentries())):
        ndocs += 1
        if ndocs > 1000:
            break        
        besttxt = DATA.joinpath(*e.fields['besttxt'].split('\\'))
        #assert besttxt.exists(), str(besttxt)
        
        rec = bibtex.Record(e.type, e.key, **e.fields)
        src = data.add(models.Document, e.key, _obj=bibtex2source(rec, cls=models.Document))
        inlgcs = re.findall("\[([a-z]{3}|NOCODE\_[A-Z][^\s\]]+)\]", e.fields.get('inlg', ''))
        src.inlg = inlgcs[0] if inlgcs else None

        i = 0
        for i, t in enumerate(get_text(besttxt).split('\f'), start=1):
            DBSession.add(models.Page(
                number=i,
                document=src,
                text=t,
                terms=func.to_tsvector(STEM.get(src.inlg, "english"), t))) #tsvector(t, e.fields.get('inlg') or '')))
        src.npages = i
         
        #
        # indexing!
        #
        nsources = {}

        langs, _ = e.languoids(langs_by_id)
        #TODO filter out non-language languoids
        src.nlangs = len(langs)
        src.langs = ' '.join({l.id for l in langs})
        for l in langs:
            if l.id not in data['GramfinderLanguage']:
                data.add(
                    models.GramfinderLanguage, l.id,
                    id=l.id, hid = l.hid, name=l.name, latitude=l.latitude, longitude=l.longitude, nsources=nsources.get(l.id, 0))

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
    langs = dict(DBSession.query(models.GramfinderLanguage.id, models.GramfinderLanguage.pk))
    for doc in DBSession.query(models.Document):
        for lid in doc.langs.split():
            DBSession.add(common.LanguageSource(source_pk=doc.pk, language_pk=langs[lid]))
