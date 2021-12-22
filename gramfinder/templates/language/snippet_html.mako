<%inherit file="../snippet.mako"/>
<%namespace name="util" file="../util.mako"/>

<h3>${h.link(request, ctx)}</h3>

% if request.params.get('q'):
    <ul>
        % for doc in ctx.sources:
            <li>
                ${h.link(req, doc)} (${doc.inlg}): matches on ${len(list(u.iter_fragments(doc, request)))} of ${doc.npages} pages
            </li>
        % endfor
    </ul>
% else:
    % if ctx.description:
        <p>${ctx.description}</p>
    % endif
${h.format_coordinates(ctx)}
% endif
