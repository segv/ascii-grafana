from grafana_terminal.session import Session
from pprint import pprint, pformat  # noqa: F401
from grafana_terminal.gnuplot import GnuPlot
import tempfile
import pystache
import re
import logging
import arrow
from copy import deepcopy


logger = logging.getLogger(__name__)


class ApplicationException(Exception):
    pass


class GrafanaAPIException(ApplicationException):
    pass


class FeatureNotSupported(ApplicationException):
    pass


class Grafana:
    def __init__(self, api_key, grafana_url):
        self.session = Session(api_key=api_key, baseurl=grafana_url)

    def get_series(self, query, start, end, step):
        res = self.session.get("/api/datasources/proxy/1/api/v1/query_range",
                               params=dict(query=query,
                                           start=min(start, end),
                                           end=max(start, end),
                                           step=step))
        json = res.json()

        status = json.get('status', None)
        if status != 'success':
            if status is None:
                raise GrafanaAPIException("Missing status")

            raise Exception(
                "API Exception: %s: %s: %s" % (json.get('status'), json.get('errorType'), json.get('error')))

        data = json['data']

        # {data: ..., status: success }
        # data: { resultType: ..., result: ... }

        resultType = data.get('resultType')
        if resultType != 'matrix':
            raise Exception("Sorry, don't know how to handle non-matrix data: %s" % resultType)

        series = data.get('result')

        if series is None or len(series) == 0:
            raise Exception("Missing results in %s" % pformat(json))

        return series

    def dashboard(self, dashboard_uid):
        return Dashboard(self, dashboard_uid)


class Dashboard:
    def __init__(self, grafana, uid, vars=None):
        self.grafana = grafana
        self.uid = uid
        if vars is None:
            vars = {}
        self.vars = vars
        self._load()

    def _parse_time_spec(self, spec):
        if spec == 'now':
            return arrow.utcnow()

        m = re.match(r'now-(\d+)([hm])', spec)  # noqa: E231
        if m:
            if m.group(1):
                qty = -1 * int(m.group(1))
                unit = m.group(2)

                if unit == 'h':
                    return arrow.utcnow().shift(hours=qty)
                elif unit == 'm':
                    return arrow.utcnow().shift(minutes=qty)
                else:
                    raise FeatureNotSupported("Can't handle time spec unit `%s` in `%s`" % (unit, spec))
            else:
                return arrow.utcnow()
        else:
            raise FeatureNotSupported("Can't handle time spec `%s`" % spec)

    def _load(self):
        res = self.grafana.session.get("/api/dashboards/uid/" + self.uid)
        if res.status_code == 404:
            raise GrafanaAPIException("Unable to find dashboard `%s`" % self.uid)

        if res.status_code != 200:
            logger.error("RES:" + pformat(res) + ":" + res.text)
            raise GrafanaAPIException("Error retreiving dashboard `%s`" % self.uid)

        data = res.json()

        dashboard = data['dashboard']

        self.time_from = self._parse_time_spec(dashboard['time']['from']).timestamp
        self.time_to = self._parse_time_spec(dashboard['time']['to']).timestamp

        templating = dashboard['templating']

        templating_keys = list(templating.keys())
        if not (templating_keys == [] or templating_keys == ['list']):
            raise FeatureNotSupported("Don't know how to parse variable key %s", templating_keys)

        self.templating = []
        for var in templating['list']:
            name = var['name']
            label = var['label']

            value = var['current']['value']
            if value == '$__all' or value == ['$__all']:
                value = '.*'

            options = [option for option in deepcopy(var['options']) if option['value'] != '$__all']
            options = [{'value': option['value'], 'text': option['text']}
                       for option in options]
            self.templating.append(dict(
                name=name,
                label=label,
                value=value,
                options=options,
            ))

        self.panels = []
        for panel in dashboard['panels']:
            type = panel['type']
            if type != 'graph':
                logger.debug("Skipping panel %s of type %s", panel['title'], type)
                continue

            self.panels.append(Graph(self, panel))


class Panel:
    pass


class Graph(Panel):
    def __init__(self, dashboard, panel_json):
        self.dashboard = dashboard
        self._load(panel_json)

    def _load(self, panel):
        if 'title' in panel:
            self.title = panel['title'].strip()
        else:
            self.title = None

        if 'description' in panel:
            self.description = panel['description'].strip()
        else:
            self.description = None

        yaxes = panel.get('yaxes')
        if yaxes:
            self.yaxes = {
                'y1': {
                    'logScale': yaxes[0].get('logBase', 1)
                },
                'y2': {
                    'logScale': yaxes[1].get('logBase', 1)
                },
            }

        self.queries = []
        for t in panel['targets']:
            if t['format'] != 'time_series':
                raise FeatureNotSupported("Sorry, can't handle non time_series graphs")

            if not t.get('hide', False):
                self.queries.append(dict(
                    expr=t['expr'],
                    legendFormat=t.get('legendFormat', None),
                ))

    def query(self):
        timestamps = set()

        metrics = []

        for q in self.queries:
            expr = q['expr']

            for t in self.dashboard.templating:
                expr = expr.replace("$" + t['name'], t['value'])

            series_data = self.dashboard.grafana.get_series(expr,
                                                            self.dashboard.time_from,
                                                            self.dashboard.time_to,
                                                            step=10)

            for i, series in enumerate(series_data):
                points = {}
                for v in series['values']:
                    timestamps.add(v[0])
                    points[v[0]] = float(v[1])

                legendFormat = q['legendFormat']
                if legendFormat is None:
                    label = pformat(series['metric'])
                else:
                    label = pystache.render(q['legendFormat'], series['metric'])

                metrics.append(dict(label=label, points=points))

        timestamps = sorted(list(timestamps))

        data = [timestamps]
        legend = []
        for metric in metrics:
            label = metric['label']
            points = metric['points']

            data.append([points.get(timestamp, '?') for timestamp in timestamps])
            legend.append(label)

        return data, legend

    def render(self, rows, cols):
        data, legend = self.query()
        gp = GnuPlot()

        with tempfile.TemporaryDirectory() as d:
            gp = GnuPlot()
            gp.c("""set terminal dumb size %s, %s enhanced""" % (cols, rows))
            # gp.c("set terminal wxt")
            gp.c("set autoscale")
            gp.c('set datafile missing "?"')
            gp.c("set xdata time")
            gp.c('set timefmt "%s"')
            if self.title is not None:
                gp.c("""set title "%s" """ % self.title)

            filename = d + "/data.txt"
            gp.s(data, filename)

            logScale1 = self.yaxes['y1']['logScale']
            if logScale1 > 1:
                gp.c('set logscale y %s' % logScale1)

            logScale2 = self.yaxes['y2']['logScale']
            if logScale2 > 1:
                gp.c('set logscale y2 %s' % logScale2)

            commands = []
            for i, label in enumerate(legend):
                commands.append('"%s" using 1:%s title "%s"' % (filename, i + 2, label))

            gp.c("plot " + ",".join(commands))
            gp.close()
