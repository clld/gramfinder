<%inherit file="${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%! multirow = True %>
<%namespace name="util" file="util.mako"/>

<div class="row-fluid">
    <h2>Search</h2>
</div>

<div class="row-fluid">
    % if hits:
        <button type="button" class="btn" data-toggle="collapse" data-target="#query">
            Show query
        </button>
    % endif
    <div id="query" class="collapse ${'' if hits else 'in'}">

    <form action="${req.url}">
        <div class="span2">
            --- Help ---
            <button type="submit" class="btn">Search</button>
        </div>
        <div class="span6">
            <legend>Search query</legend>
            % for iso, name, count in inlgs:
                <p>
                    <input type="text" id="query${iso}" name="query-${iso}" placeholder="query"
                           class="search-query"
                           value="${q.get(iso) or ''}"> <span>${name} documents (${count})</span>
                </p>
            % endfor
        </div>
        <div class="span4">
            <legend>Document types</legend>
            % for dt, selected in doctypes:
                <label class="checkbox">
                    <input type="checkbox" name="dt-${dt.id}" value="" ${'checked' if selected else ''}>
                    ${dt.name} (${dt.ndocs})
                </label>
            % endfor
        </div>
    </form>
    </div>
</div>

<div class="row-fluid">
    % if hits:
        <h3>
            ${len(by_lg)} languoids with matching descriptions
        </h3>

    ${map.render()|n}

        <table class="table table-nonfluid">
            <thead>
            <tr>
                <th>Language</th>
                <th>Matches</th>
                <th>Sources</th>
                <th></th>
            </tr>
            </thead>
            <tbody>
                % for lid, docs in by_lg.items():
                    <tr>
                        <td>
                            ${h.link(req, langs[lid])}
                        </td>
                        <td>
                            ${sum(c for _, c in docs)}
                        </td>
                        <td>
                            ${len(docs)}
                        </td>
                        <td>
                            <a onclick="$('#detail-${lid}').toggle()">details</a>
                        </td>
                    </tr>
                    <tr id="detail-${lid}" style="display: none">
                        <td colspan="4">
                            <ul>
                                % for doc, c in docs:
                                    <li>${h.link(req, doc)}
                                        matches on ${c} pages
                                        <a onclick="$('#doc-${doc.pk}').load('${req.route_url('source_alt', id=doc.id, ext='snippet.html', _query={'query-{}'.format(k): v for k, v in q.items() if k == doc.inlg or k == 'any'})}');">
                                            show</a>
                                        <div id="doc-${doc.pk}"></div>
                                    </li>
                                % endfor
                            </ul>
                        </td>
                    </tr>
                % endfor
            </tbody>
        </table>
    % endif
</div>