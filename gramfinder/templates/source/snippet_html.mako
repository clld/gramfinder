<%inherit file="../snippet.mako"/>

<ul>
    % for p, f in pages:
        <li>
            page ${p.number}
            ${f|n}
        </li>
    % endfor
</ul>