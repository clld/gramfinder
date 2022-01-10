<%inherit file="${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="util.mako"/>

<form class="form-search" action="${req.url}">
<div class="row-fluid">

<div class="span3">
<table class="table table-nonfluid">
    <tbody>
% for i in range(10):
    <tr id="query-${i}" style="display: ${'none' if (i > 0 and not qs.get('%s' % i)) else ''}">
    <td>
    <select name="${'s_%s' % i}" style="width: 100px;">
        % for inlgname, inlg in inlgs + [("Any", "ANY")]:
            <option value="${inlg}" ${'selected' if inlg == qlgs.get('%s' % i) else ''}>${inlgname}</option>
        % endfor
    </select>
    </td>
    <td>
    <input name="${'q_%s' % i}" type="text" class="input-medium search-query" value="${qs.get('%s' % i, '')}">
    </td>
   <td style="display: ${'none' if i == 9 else ''}">
        <a onclick="$('#query-${str(i+1)}').toggle()">&plusmn;</a>
   </td>
    </tr>
% endfor
    </tbody>
</table>

    <button type="submit" class="btn">Search</button>
</div>

<div class="span3 well well-small">
<table class="table table-nonfluid">
    <thead>
    <tr>
        <th></th>
        <th colspan=2>Document types to include</th>
    </tr>
    </thead>
    <tbody>
        % for (dt, dt_ndocs, dt_check) in doctypes:
            <tr>
               <td class="left">
               <label class="checkbox">
               <input type="checkbox" name="${dt}" ${'checked' if dt_check else ''}>
               </label></td>
               <td class="left">${dt.replace("_", " ")}</td>
               <td class="right">${dt_ndocs}</td>
            </tr>
        % endfor
    </tbody>
</table>


</div>


</form>
</div>



<div class="row-fluid">

% if hits:
    <h3>
        ${len(by_lg)} languoids with descriptions matching the query:
    </h3>

<table class="table table-nonfluid">
        <thead>
        <tr>
% for n, q in qs.items():
<td>${qlgs[n]}</td>
% endfor
        </tr>
        </thead>
    <tbody>
        <tr>
% for n, q in qs.items():
<td>${q}</td>
% endfor
        </tr>
    </tbody>
</table>

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

</div>