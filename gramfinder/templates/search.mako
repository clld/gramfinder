<%inherit file="${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="util.mako"/>


<form class="form-search" action="${req.url}">
    <input name="q" type="text" class="input-medium search-query" value="${q}">
    <button type="submit" class="btn">Search</button>
</form>

% if hits:
    ${map.render()|n}
    <p>
        ${len(by_lg)} languoids with descriptions matching the query "${q}"
    </p>
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
                                    <a onclick="$('#doc-${doc.pk}').load('${req.route_url('source_alt', id=doc.id, ext='snippet.html', _query=dict(q=q))}');">
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
