from clld.web.maps import Map, Layer
from clld.web.adapters import geojson
from clldutils import svg


class GeoJsonLanguages(geojson.GeoJson):
    def feature_iterator(self, ctx, req):
        yield from self.obj[0]

    def feature_properties(self, ctx, req, feature):
        return {'icon': svg.data_url(svg.icon(self.obj[1][feature.id].replace('#', 'c')))}


class SearchMap(Map):
    def get_layers(self):
        yield Layer(
            'm',
            'languages',
            GeoJsonLanguages(self.ctx).render(self.ctx, self.req, dump=False),
        )
