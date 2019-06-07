# ascii-grafana

Renders a grafana dashboard (and panels), such as:

![screenshot from browser](./docs/assets/grafana.png)

as ascii text in a terminal:

```
$ ascii-grafana dashboard --api-key "eyJrIjoidFZMOWsyMDlzQnQzZXk2VW9XVEwxMTRZM2NJWm4wakoiLCJuIjoibWFyY28tdGVzdCIsImlkIjoxfQ==" --grafana-url "https://grafana.rps-infra.com" --dashboard "riZ9VxWZk"

                                        active accounts

  25000 +-+---+-----+-----+-----+-----+-----+-----+----+-----+-----+-----+-----+-----+---+-+
        +           +           +           +          +           +           +           +
        |                                                                       BBBB       |
        |                                       BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB          |
  20000 +-+                                 BBBBB                                        +-+
        |                                   B                                              |
        |                             BBBBBBB                                              |
        |                             B                                                    |
  15000 +-+                       BBBBB                                                  +-+
        |                        BB                                                        |
        |                        B                                                         |
        |                                                                                  |
        |                       B                                                          |
  10000 +-+                  BBBB                                                        +-+
        |                BBBBB                                                             |
        |           BBBBBB                                                                 |
        |           B                                                                      |
   5000 +-+ BBBBBBBBB                                                                    +-+
        |                                                                                  |
        |                                                                       EEEE       |
        +           +           +           +     EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE          +
      0 +-+-CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAAAAAAA-+---+-+
      01:00       02:00       03:00       04:00      05:00       06:00       07:00       08:00
```

See the cli help for details:

```
$ ascii-grafana dashboard --help
Usage: ascii-grafana dashboard [OPTIONS]

  Renders a given grafana dashboard to the terminal. The panels of the
  dashboard, of the types supported by ascii-grafana, will be printed one
  after the other as ascii.

Options:
  -d, --dashboard TEXT    UID of the dashboard to render.  [required]
  -r, --rows INTEGER      Number of rows to render, defaults to terminal's
                          size.
  -c, --cols INTEGER      Number of cols to render, defaults to terminal's
                          size.
  -l, --loop INTEGER      If present specifies the number of seconds to wait
                          between
                          rendering panels of the dashboard. If not
                          provided every dashboard panel will be rendered
                          exactly once and then the command will
                          terminate.
  -k, --api-key TEXT      Grafana API KEY. Must have view access to the
                          dashboard. Example:
                          eyJrIjoidFZMOWsyMDlzQnQzZXk2VW9X
                          VEwxMTRZM2NJWm4wakoiLCJuIjoibWFyY28tdGVzdCIsImlkIjox
                          fQ==
                          Passed via env var AG_API_KEY as well.
                          [required]
  -u, --grafana-url TEXT  Base URL for the grafana instance. Example:
                          https://grafana.example.com. Passed via env var
                          AG_GRAFANA_URL as well.  [required]
  --help                  Show this message and exit.
```
