1. Update version to, e.g. 1.0.0 in ``altair_viewer/__init__.py``

2. Make sure ``CHANGES.md`` is up to date for the release

3. Commit change and push to master

       git add . -u
       git commit -m "MAINT: bump version to 1.0.0"
       git push upstream master

4. Tag the release:

       git tag -a v1.0.0 -m "version 1.0.0 release"
       git push upstream v1.0.0

5. Build source & wheel distributions

       rm -r dist build  # clean old builds & distributions
       python setup.py sdist  # create a source distribution
       python setup.py bdist_wheel  # create a universal wheel

6. publish to PyPI (Requires correct PyPI owner permissions)

       twine upload dist/*

7. update version to, e.g. 1.1.0.dev0 in ``altair_viewer/__init__.py``

8. add a new changelog entry for the unreleased version

9. Commit change and push to master

       git add . -u
       git commit -m "MAINT: bump version to 1.1.0.dev0"
       git push origin master
