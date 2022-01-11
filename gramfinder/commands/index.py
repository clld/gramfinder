"""
"""
import transaction
from sqlalchemy import or_, func, not_
from clld.db.meta import DBSession
from clld.cliutil import AppConfig, SessionContext
from clldutils.clilib import PathType
from tqdm import tqdm
from unidecode import unidecode

from gramfinder import models
from gramfinder.config import stemmer


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


def register(parser):
    parser.add_argument('config', action=AppConfig)
    parser.add_argument(
        'data_dir',
        help="",
        type=PathType(type='dir'))
    parser.add_argument('--max-docs', type=int, default=None)


def index(dpk, besttxt, inlg):
    i = 0
    for i, t in enumerate(besttxt.split('\f'), start=1):
        DBSession.add(models.Page(
            number=i,
            document_pk=dpk,
            text=t,
            terms=func.to_tsvector(stemmer(inlg), t)))
    models.Document.get(dpk).npages = i


def run(args):  # pragma: no cover
    count, stop = 0, False
    with SessionContext(args.settings):
        with transaction.manager:
            with_pages = set(r[0] for r in DBSession.query(models.Page.document_pk).distinct())
            docs = [(d.pk, d.besttxt, d.inlg) for d in DBSession.query(models.Document).filter(not_(models.Document.pk.in_(with_pages)))]

        chunks = [docs[i:i + 10] for i in range(0, len(docs), 10)]
        for chunk in tqdm(chunks, total=len(chunks)):
            with transaction.manager:
                for dpk, txt, inlg in chunk:
                    if txt:
                        index(dpk, get_text(args.data_dir.joinpath(txt)), inlg or '')
                        count += 1
                        if args.max_docs and count > args.max_docs + 1:
                            stop = True
                            break
            if stop:
                break
