# Building the documentation

The build the documentation install the package using poetry with the doc group and all extras:

```shell
poetry install --all-extras --with=doc
```

Before building the documentation with mkdocs, pre-process script must be run to generate a number of dynamic required files. Run from the repository root either

```shell
python docs/dump_github_releases.py
python docs/generate_visualization_examples.py
```

or

```shell
make doc-preprocess
```