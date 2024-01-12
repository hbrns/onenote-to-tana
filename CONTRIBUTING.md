# Contributing guidelines

Any contribution is appreciated! You might want to:

* Fix spelling errors
* Improve documentation
* Add tests for untested code
* Add new features
* Fix bugs

## How can I contribute?

* Use [issues](https://github.com/hbrns/onenote-to-tana/issues) to report bugs and features
    - If you report a bug in the results for a particular OneNote, include that .one. This allows others to replicate the issue. 
* Fix issues by [creating pull requests](https://help.github.com/en/articles/creating-a-pull-request).
* Help others by sharing your thoughs in comments on issues and pull requests.

## Guideline for creating issues

* Search previous issues, as yours might be a duplicate.
* When creating a new issue for a bug, include a minimal reproducible example.
* When creating a new issue for a feature, be sure to describe the context of the problem you are trying to solve. This
  will help others to see the importance of your feature request. 

## Guideline for creating pull request

* A pull request should close an existing issue. For example, use "Fix #123" to indicate that your PR fixes issue 123. 
* Pull requests should be merged to master.
* Include unit tests when possible. In case of bugs, this will help to prevent the same mistake in the future. In case
  of features, this will show that your code works correctly.
* Code should work for Python 3.11+.
* Test your code. <!-- by using nox (see below). -->
* New features should be well documented using docstrings.
* Check if the [README.md](README.md) <!-- or [readthedocs](../docs/source)  --> documentation needs to be updated.
* Check spelling and grammar.

### Certificate of origin

In order to get a clear contribution chain of trust we use the
[signed-of-by language](https://www.kernel.org/doc/html/latest/process/submitting-patches.html#sign-your-work-the-developer-s-certificate-of-origin)
used by the Linux kernel project.
Please make sure your commit message adheres to this guideline.

## Guideline for posting comments

* [Be cordial and positive](https://kennethreitz.org/essays/2013/01/27/be-cordial-or-be-on-your-way)

## Guideline for dependencies

* This package is distributed under the [MIT license](LICENSE).
* All dependencies should be compatible with this license.
* Use [licensecheck](https://pypi.org/project/licensecheck/) to validate if new packages are compatible.

## Getting started

1. Clone the repository

    ```sh
    git clone https://github.com/hbrns/onenote-to-tana.git
    cd onenote_to-tana
    ```

2. Install dev dependencies

    ```sh
    poetry install --with=dev
    ```

3. Run the tests

    ```sh
    cd onenote_to-tana
    python convert_to_tif.py --help
    ```

<!--
    On all Python versions:

    ```sh
    nox
   ```
-->
