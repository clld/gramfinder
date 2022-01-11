import functools
import collections

from pyramid.config import Configurator

from clld.interfaces import IMapMarker, IValueSet, IValue, IDomainElement
from clldutils.svg import pie, icon, data_url
from clld.web import app
from clld_glottologfamily_plugin.util import LanguageByFamilyMapMarker

# we must make sure custom models are known at database initialization!
from gramfinder import models
from gramfinder import views
from gramfinder import datatables


class MapMarker(LanguageByFamilyMapMarker):
    pass


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('clld.web.app')
    config.include('clld_glottologfamily_plugin')
    config.registry.registerUtility(MapMarker(), IMapMarker)
    config.add_route_and_view('search', '/search', views.search, renderer='search.mako')
    config.register_menu(
        ('dataset', functools.partial(app.menu_item, 'dataset', label='Home')),
        ('search', functools.partial(app.menu_item, 'search', label='Search')),
        ('languages', functools.partial(app.menu_item, 'languages', label='Languages')),
        ('sources', functools.partial(app.menu_item, 'sources', label='Sources')),
    )

    return config.make_wsgi_app()
