
Load the bib data:
```shell
clld initdb development.ini --glottolog ~/projects/glottolog/glottolog
```

Index the text data:
```shell
gramfinder index development.ini .. --max-docs 1000
```

