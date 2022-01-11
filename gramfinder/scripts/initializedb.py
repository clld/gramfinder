import pathlib
import itertools

from sqlalchemy.orm import joinedload
import tqdm
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clld.db import fts
from unidecode import unidecode
from pyglottolog import Glottolog
from clld_glottologfamily_plugin.util import load_families

import gramfinder
from gramfinder.config import INLGS
from gramfinder import models

DATA = pathlib.Path(__file__).parent.parent.parent.parent.joinpath("dbs\\") if pathlib.Path(__file__).parent.parent.parent.parent.joinpath("dbs").exists() else pathlib.Path(__file__).parent.parent.parent.parent.joinpath("more")


def get_inlg(s):
    for k in INLGS:
        if '[{}]'.format(k) in s:
            return k
    return None


def main(args):
    global DATA

    datadir = input('Data [{}]: '.format(str(DATA)))
    if datadir:
        DATA = pathlib.Path(datadir)

    maxdocs = input('Max number of bib records with texts to load [1000]: ')
    maxdocs = int(maxdocs or 1000)

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
    recs = []
    for n, e in enumerate(tqdm.tqdm(itertools.filterfalse(
            lambda i: not i.fields.get('besttxt'), bib.iterentries()), desc='reading hh.bib')):
        if n >= maxdocs:
            break
        recs.append(e)

    for e in recs:
        for ht in e.doctypes(dt_by_id)[0]:
            htndocs[ht.id] = htndocs.get(ht.id, 0) + 1
 
    for ht in gl.hhtypes:
        if htndocs.get(ht.id, 0) > 0:
            data.add(
                models.Doctype, ht.id, id=ht.id, name=ht.name, description=ht.description, rank=ht.rank, ndocs = htndocs[ht.id])

    langs_by_id = gl.languoids_by_code()

    ndocs = 0
    for e in recs:
        ndocs += 1
        besttxt = DATA.joinpath(*e.fields['besttxt'].split('\\'))
        #assert besttxt.exists(), str(besttxt)
        
        rec = bibtex.Record(e.type, e.key, **e.fields)
        obj = bibtex2source(rec, cls=models.Document)
        obj.id = unidecode(e.key).replace(':', '_').replace('-', '_')
        src = data.add(models.Document, e.key, _obj=obj)
        src.inlg = get_inlg(e.fields.get('inlg') or '')
        src.besttxt = '/'.join(e.fields['besttxt'].split('\\')) if besttxt.exists() else None
        if not src.besttxt:
            print(e.fields['besttxt'])

        #
        # indexing!
        #

        langs, _ = e.languoids(langs_by_id)
        langs = [l for l in langs if l.level.name == 'language']
        src.nlangs = len(langs)
        src.langs = ' '.join({l.id for l in langs})
        for l in langs:
            if l.id not in data['GramfinderLanguage']:
                data.add(
                    models.GramfinderLanguage, l.id,
                    id=l.id,
                    hid=l.hid,
                    name=l.name,
                    latitude=l.latitude,
                    longitude=l.longitude,
               )
        for ht in e.doctypes(dt_by_id)[0]:
            DBSession.add(models.DocumentDoctype(document=src, doctype=data['Doctype'][ht.id]))

    load_families(data, data['GramfinderLanguage'].values(), glottolog_repos=gl.repos)


def prime_cache(args):
    langs = dict(DBSession.query(models.GramfinderLanguage.id, models.GramfinderLanguage.pk))
    for doc in DBSession.query(models.Document)\
            .options(
                joinedload(models.Document.doctype_assocs)
                .joinedload(models.DocumentDoctype.doctype)):
        for lid in doc.langs.split():
            DBSession.add(common.LanguageSource(source_pk=doc.pk, language_pk=langs[lid]))
        types = sorted([dta.doctype for dta in doc.doctype_assocs], key=lambda dt: -dt.rank)
        if types:
            doc.maxrank = types[0].rank
            doc.types = ' '.join(dt.id for dt in types)

    for lang in DBSession.query(models.GramfinderLanguage)\
            .options(joinedload(models.GramfinderLanguage.sources)):
        lang.nsources = len(lang.sources)

    for dt in DBSession.query(models.Doctype)\
            .options(joinedload(models.Doctype.document_assocs)):
        dt.ndocs = len(dt.document_assocs)
