# Contributing to nightjar-mesh

First, you need to agree to submit your code under the [license](LICENSE).

## Principals



## Style Guidelines

## Pass All Tests

For the Python code, the code must:

* Pass unit test.
    * `cd nightjar && python3 -m coverage run --source . -m unittest discover`
* And code coverage must not go down.
    * `cd nightjar && python3 -m coverage report -m`
* Pass mypy checks.
    * `cd nightjar && mypy --warn-redundant-casts --ignore-missing-imports --warn-unused-ignores generate-envoy-proxy.py`
    * This requires installing the `test-requirements.txt` locally.

To help out with this, I recommend setting up a virtual environment locally:

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

Now you can submit a PR to the main project.

