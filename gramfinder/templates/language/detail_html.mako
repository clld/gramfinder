<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "languages" %>
<%block name="title">${_('Language')} ${ctx.name}</%block>

<h2>${_('Language')} ${ctx.name}</h2>

% if hits:
    <p>
        <button type="button" class="btn" data-toggle="collapse" data-target="#query">
            Show/hide query
        </button>
    </p>
% endif
<div id="query" class="collapse ${'' if hits else 'in'}">
    <form action="${req.url}">
        <table class="table table-nonfluid">
    <thead>
        <tr><td></td><th>Source</th><th>Meta language</th><th>Document type</th><th>Pages</th></tr>
    </thead>
    % for src in ctx.sorted_sources:
        <tr>
            <td>
                <input type="text" name="query-${src.pk}" placeholder="query"
                       class="search-query"
                       value="${req.params.get('query-{}'.format(src.pk)) or ''}">
            </td>
            <td>${h.link(req, src)}: ${src.description}</td>
            <td>${src.inlg}</td>
            <td>${src.maxtype.id.replace('_', ' ')}</td>
            <td>${src.npages}</td>
        </tr>
    % endfor
    </table>
    <p>
        <button type="submit" class="btn">Search</button>
    </p>
    </form>
</div>

% if hits:
    <div class="accordion" id="accordion2">
    % for doc, pages in hits:
        <div class="accordion-group">
            <div class="accordion-heading">
                <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapse${loop.index}">
                    ${doc.name}:
                    ${sum(sum(f.count('<span style=') for f in fs) for _, fs in pages)} matches
                    for <emph>${req.params.get('query-{}'.format(doc.pk)) or ''}</emph>
                    on ${len(pages)} pages)
                </a>
            </div>
            <div id="collapse${loop.index}" class="accordion-body collapse${' in' if loop.first else ''}">
                <div class="accordion-inner">
                    <table class="table">
                        <thead>
                        <tr>
                            <th>page</th>
                            <th>matches</th>
                        </tr>
                        </thead>
                        <tbody>
                            % for p, fs in pages:
                                <tr>
                                    <td>
                                        ${p.number}
                                        % if 'fn' in doc.jsondatadict:
                                            <a href="${doc.jsondata['fn']}#${p.number}">[PDF]</a>
                                        % endif
                                    </td>
                                    <td>
                                        <ul class="unstyled">
                                        % for f in fs:
                                            <li>…${f|n}…</li>
                                        % endfor
                                        </ul>
                                    </td>
                                </tr>
                            % endfor
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    % endfor

    </div>
% endif

<%def name="sidebar()">
    ${util.language_meta()}
</%def>
