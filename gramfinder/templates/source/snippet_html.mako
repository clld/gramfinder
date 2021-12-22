<%inherit file="../snippet.mako"/>

<ul>
    % for p, f in u.iter_fragments(ctx, req):
        <li>
            page ${p.number}
            ${f|n}
        </li>
    % endfor
</ul>