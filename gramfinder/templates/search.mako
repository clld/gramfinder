<%inherit file="${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="util.mako"/>
<%block name="head">
    <link href="${request.static_url('clld:web/static/css/select2.css')}"
          rel="stylesheet">
    <script src="${request.static_url('clld:web/static/js/select2.js')}"></script>
</%block>

<%def name="sidebar()">
    <div class="well">
        <form class="form-horizontal" action="${req.url}">
            <legend>Search query</legend>
            % for name, iso in inlgs:
                <div class="control-group">
                    <label class="control-label" for="query${iso}">${name}</label>
                    <div class="controls">
                        <input type="text" id="query${iso}" name="query-${iso}" placeholder="query" class="search-query"
                               value="${q.get(iso) or ''}">
                    </div>
                </div>
            % endfor
            <div class="control-group">
                <label class="control-label" for="queryany">Any language</label>
                <div class="controls">
                    <input type="text" id="queryany" name="query-any" placeholder="query" class="search-query"
                           value="${q.get('any') or ''}">
                </div>
            </div>

            <div class="control-group">
                <label class="control-label" for="doctypes">Document types</label>
                <div class="controls">
                    ${ms.render()|n}
                    <span class="help-block">Start typing the document type in the field above.</span>
                </div>
            </div>

            <div class="control-group">
                <div class="controls">
                    <button type="submit" class="btn">Search</button>
                </div>
            </div>

        </form>
    </div>
</%def>


    <h2>Search</h2>

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
            <th> </th>
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
