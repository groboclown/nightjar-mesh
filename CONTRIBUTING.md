# Contributing to nightjar-mesh

First, you need to agree to submit your code under the [license](LICENSE).

## Principles

Nightjar strives to:

* Keep the number of containers small.  If possible, run the Nightjar tools inside the Envoy proxy container.
* Keep the Nightjar footprint small.  It should attempt to keep memory and CPU usage down.  If possible, also keep the docker image size small.
* Be compatible with docker containers running in bridge network mode.
* Keep the Envoy configuration transparent.  If Nightjar moves to being a proper control mesh, and talks to the dynamic configuration capabilities of Envy, then the configuration should continue to be generated based on user-modifiable data input that matches the Envoy API.
* Document all the configurable aspects.
* Keep the documentation clear and complete.


## Style Guidelines

For Python, conform to the PEP8 style where possible.  Also, use mypy-conformant typing.

Shell scripts and yaml files use 2 spaces for indenting, while Python uses 4 spaces.

Keep the functionality in the right place.  Where possible, have tools that do one thing, and keep track of what they did to give end-users insight into what the tools did.


## Pass All Criteria

(This needs to change.  The code is undergoing major restructuring to allow for different modes of operation.)

The code must:

* Pass Python unit tests.
    * `cd nightjar-src && python3 -m coverage run --source . -m unittest discover`
* And code coverage must not go down.
    * `cd nightjar-src && python3 -m coverage report -m generate_template_input_data.py`
    * `python3 -m coverage json && jq '.files."generate_template_input_data.py".summary.percent_covered' < coverage.json`
* Pass mypy checks.
    * `cd nightjar-src && mypy --warn-redundant-casts --ignore-missing-imports --warn-unused-ignores generate_template_input_data.py`
* Pass shell script tests.
    * `docker build -t my/nightjar-test -f Dockerfile.shell-test . && docker run -it --rm my/nightjar-test`
* The docker image constructs without failures.
    * `docker build -t my/nightjar .`

You will need to install the required Python modules to run the Python tests.  See the development environment section below to help get them installed.


## Submission

You will need to fork the project in GitHub so that you can submit a Pull Request.

Once you have the forked project, clone it down to your computer and create a new branch off of the dev branch.

```bash
$ git clone git@github.com:my-personal-project/nightjar-mesh.git
$ cd nightjar-mesh
$ git checkout -b my-great-improvement dev
```

Now you're ready to get working!

Once you have your changes in place, you can optionally "squash" them into a single change to make reviewing easier.  But you don't have to.

```bash
$ git checkout -b descriptive-name-of-change dev
$ git merge --squash my-great-improvement
$ git push origin descriptive-name-of-change
```

Your GitHub project is now ready for you to submit a PR.


## Development Environment

Here's the easy way to get your development environment in a place to get working.

```bash
$ cd /my/path/to/nightjar-mesh
$ python3 -m venv venv
$ . venv/bin/activate
$ python3 -m pip install --upgrade pip
$ python3 -m pip install -r nightjar/requirements.txt
$ python3 -m pip install -r nightjar/test-requirements.txt
```

For Windows users, it's a bit different.

```powershell
PS > cd \my\path\to\nightjar-mesh
PS > python -m venv venv
PS > venv\Scripts\Activate.ps1
PS > python -m pip install --upgrade pip
PS > python -m pip install -r nightjar/requirements.txt
PS > python -m pip install -r nightjar/test-requirements.txt
```
