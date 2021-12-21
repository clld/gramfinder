<ul>
    % for p, f in pages:
        <li>
            ${p.number}, ${p.label or ''}
            ${f|n}
        </li>
    % endfor
</ul>