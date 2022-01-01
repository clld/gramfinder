import pathlib
import itertools

import tqdm
from clld.cliutil import Data, bibtex2source
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib import bibtex
from clld.db import fts
from pyglottolog.references import BibFile
from pyglottolog import Glottolog
from unidecode import unidecode

import gramfinder
from gramfinder import models

DATA = pathlib.Path(__file__).parent.parent.parent.parent.joinpath("dbs\\") if pathlib.Path(__file__).parent.parent.parent.parent.joinpath("dbs\\").exists() else pathlib.Path(__file__).parent.parent.parent.parent

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

    gl = Glottolog(args.glottolog or "..\\glottolog\\")
    #bib = BibFile(DATA.joinpath('hh10000.bib'))
    bib = gl.bibfiles['hh']
    dt_by_id = {}
    for ht in gl.hhtypes:
        dt_by_id[ht.id] = ht
        data.add(
            models.Doctype, ht.id, id=ht.id, name=ht.name, description=ht.description, rank=ht.rank)
    langs_by_id = gl.languoids_by_code()

    for e in tqdm.tqdm(itertools.filterfalse(
            lambda i: not i.fields.get('besttxt'), bib.iterentries())):
        besttxt = DATA.joinpath(*e.fields['besttxt'].split('\\'))

        rec = bibtex.Record(e.type, e.key, **e.fields)
        obj = bibtex2source(rec, cls=models.Document)
        obj.id = unidecode(e.key).replace(':', '_').replace('-', '_')
        src = data.add(models.Document, e.key, _obj=obj)
        src.inlg = e.fields.get('inlg')
        src.besttxt = '/'.join(e.fields['besttxt'].split('\\')) if besttxt.exists() else None
        if not src.besttxt:
            print("MISSING", e.fields['besttxt'], DATA, besttxt)
            break
g        #
        # indexing!
        #

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
