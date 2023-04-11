# Releasing a new version

* Push your changes to origin
* Document your changes in ~/docs/gui-executor.adoc
* Run `asciidoctor -r asciidoctor-tabs -o index.html gui-executor.adoc`
* Push doc changes to origin
* Bump the version in `__version__.py` 
* Push the bumped version
* Upload to PyPI
  ```
  $ python3 setup.py upload
  ```
* Create a pull request and merge the pull request
* Push the tags to upstream
  ```
  $ git push --tags push-tags
  ```
