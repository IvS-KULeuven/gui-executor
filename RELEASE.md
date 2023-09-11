# Releasing a new version

* Push your changes to origin
* Document your changes in ~/docs/gui-executor.adoc
* Run `asciidoctor -r asciidoctor-tabs -o index.html gui-executor.adoc`
* Push doc changes to origin
* Bump the version in `__version__.py` 
* Push the bumped version
* Upload to PyPI
  ```
  $ python -m build
  $ twine upload dist/gui-executor-x.y.z.tar.gz dist/gui_executor-x.y.z-py3-none-any.whl
  $ git tag x.y.z
  ```
* Create a pull request and merge the pull request
* Push the tags to upstream
  ```
  $ git push --tags push-tags
  ```
