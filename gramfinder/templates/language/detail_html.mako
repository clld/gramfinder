<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "languages" %>
<%block name="title">${_('Language')} ${ctx.name}</%block>

<h2>${_('Language')} ${ctx.name}</h2>

<table class="table table-nonfluid">
    <thead>
        <tr><th>Source</th><th>Document type</th><th>Pages</th></tr>
    </thead>
    % for src in ctx.sorted_sources:
        <tr>
            <td>${h.link(req, src)}</td>
            <td>${src.maxtype.name}</td>
            <td>${src.npages}</td>
        </tr>
    % endfor
</table>

<%def name="sidebar()">
    ${util.language_meta()}
</%def>
