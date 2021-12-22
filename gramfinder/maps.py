from clld.web.maps import Map, Layer, Legend
from clld.web.adapters import geojson
from clld.web.util.htmllib import HTML
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

    def get_options(self):
        res = Map.get_options(self)
        res['info_query'] = dict(q=self.req.params.get('q'))
        return res

    def _colorbar(self):
        return HTML.table(*[
            HTML.tr(
                HTML.td(' ', class_='colorbar', style='background-color: ' + color),
                HTML.td(label or ''))
            for label, color in self.ctx[2]])

    def get_legends(self):
        yield from Map.get_legends(self)
        yield Legend(
            self,
            'values',
            [HTML.div(
                HTML.p('Number of matching pages in descriptive sources'),
                self._colorbar(),
                class_='colorbar')],
            label='Legend',
            stay_open=True,
        )