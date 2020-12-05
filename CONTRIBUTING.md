# Contributing

Thank you for you interest in contributing! There are just a few things 😉

Every code seek to be performant, usable, stable and maintainable.
This can only be achieve through high test coverage, good documentation and
coding consistency. Isn't it frustrating when you cannot understand some code
just because there is no documentation nor any test to assess that the function
is working nor any comments in the code itself? How are you supposed to code in
these conditions?

To contribute, you **must** comply to the following rules for your
pull request (PR) to be considered.

## TL;DR

* All code should have tests.
* All code should be documented.
* No changes are ever committed without review and approval by a core team member.

## Project management

* For a PR to be integrated, it must be approved at least by one core team member.
* Continuous Integration is provided by *Github actions* and configuration is located at ``.github/workflows``.

## Code

### Style

For all python code, developers **must** follow guidelines from the Python Software Foundation. As a quick reference:

* For code: [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* For documentation: [PEP 257](https://www.python.org/dev/peps/pep-0257/)
* Use reStructuredText formatting: [PEP 287](https://www.python.org/dev/peps/pep-0287/)

> While we strive to document the best the code. Documenting obvious things obfuscates more than it helps. A good code is readable and somehow self-explanatory.

And for a more Pythonic code: [PEP 20](https://www.python.org/dev/peps/pep-0020/)
Last but not least, avoid common pitfalls: [Anti-patterns](https://docs.quantifiedcode.com/python-anti-patterns/)

### Linter

Appart from normal unit and integration tests, you can perform a static
analysis of the code using *black*, *flake8* and *isort* using *pre-commit* hooks:

```bash
pre-commit install
pre-commit run --all-files
```

This allows to spot naming errors for example as well as other style errors.

### Testing

Testing your code is paramount. Without continuous integration, you **cannot**
guaranty the quality of the code. Some minor modification on a module can have
unexpected implications. With a single commit, everything can go south!
The ``master`` branch is always on a passing state. This means that you should be able to checkout from main an use the code without any errors.

The library [pytest](https://docs.pytest.org/en/latest/) is used. It is simple and powerful.
Checkout their doc and replicate constructs from existing tests. If you are not already in love with it, you will soon be.

On top of pytest we use [coverage](https://coverage.readthedocs.io/) to ensure the added functionalities are covered by tests.

All tests can be launched using:

```bash
pytest --cov
```

The output consists in tests results and coverage report.

> Tests will be automatically launched when you will push your branch to the server. So you only have to run locally your new tests or the one you think you should.

## GIT

### Workflow

The development model is based on the Cactus Model also called [Trunk Based Development](https://trunkbaseddevelopment.com) model. More specificaly, we use the Scaled Trunk-Based Development model.

> Some additional ressources: [gitflow](https://nvie.com/posts/a-successful-git-branching-model/), [gitflow critique](https://barro.github.io/2016/02/a-succesful-git-branching-model-considered-harmful/), [github PR](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-request-merges).

It means that **each** new feature has to go through a new branch. Why? For peer review. Pushing directly on the develop without review should be exceptional (hotfix)!

This project is using pre-commit hooks. So you have to set it up like this:

```bash
pre-commit install
pre-commit run --all-files
```
When you try to commit your changes, it will launch the pre-commit hooks (``.pre-commit-config.yaml``)
and modify the files if there are any changes to be made for the commit to be accepted.
If you don't use this feature and your changes are not compliant (linter), CI will fail.

### Recipe for new feature

If you want to add a modification, create a new branch branching off ``master``.
Then you can create a merge request on *github*. From here, the fun begins.
You can commit any change you feel, start discussions about it, etc.

Here is how it works:

1. Clone the project to your local disk:

   ```bash
   git clone https://github.com/tupui/apophis
   ```

2. Create a branch to hold your changes:

   ```bash
   git checkout -b my-feature
   ```

   and start making changes. Never work in the ``master`` branch!

3. Work on this copy, on your computer, using Git to do the version
   control. When you're done editing, do:

   ```bash
   git add modified_files
   git commit
   ```

   to record your changes in Git, then push them to github with:

   ```bash
   git push -u origin my-feature
   ```

5. Finally, create a merge request.

> For every commit you push, the linter and tests are launched.

Your request will only be considered for integration if in a **finished** state:

1. Respect python coding rules,
2. Maintain linting score,
3. Have tests regarding the changes,
4. The branch passes all tests (current and new ones),
5. Maintain test coverage,
6. Have the respective documentation.
