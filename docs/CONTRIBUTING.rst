===================
Contributor's Guide
===================

If you are reading this, you're probably interested in contributing to this
project. All contributions are welcome and your efforts are greatly
appreciated. This document lays out guidelines and advice for contributing to
the project.

Note that the project maintainers have the final say on whether or not a
contribution is accepted. All contributions will be considered carefully, but
occasionally, some contributions will be rejected because they do not suit the
current goals or needs of the project.

If your contribution is rejected, don't despair! As long as you followed these
guidelines, you will have a much better chance of getting your next
contribution accepted.

Steps for Submitting Code
~~~~~~~~~~~~~~~~~~~~~~~~~

Use the checklist below when contributing code:

1. Fork the repository on `GitHub`_.
2. Run the tests to confirm they all pass on your system. If they don't, you'll
   need to investigate why they fail. If you're unable to diagnose this
   yourself, raise it as a bug report by creating a new issue on GitHub.
3. Write tests that demonstrate your bug or feature. Ensure that they fail.
4. Make your change.
5. Run the entire test suite again, confirming that all tests pass including
   the ones you just added. Send a GitHub Pull Request to the main repository's
   ``main`` branch. GitHub Pull Requests are the expected method of code
   collaboration on this project.

Code Review
~~~~~~~~~~~

Contributions will not be merged until they've been code reviewed. You should
implement any code review feedback unless you strongly object to it. In the
event that you object to the code review feedback, you should make your case
clearly and calmly. If, after doing so, the feedback is judged to still apply,
you must either apply the feedback or withdraw your contribution.

Code Style
~~~~~~~~~~

This project uses a collection of tools to ensure the code base has a
consistent style as it grows. We have these orchestrated using a tool called
`pre-commit`_. This can be installed locally and run over your changes prior
to opening a PR, and will also be run as part of the CI approval process
before a change is merged.

You can find the full list of formatting requirements specified in the
`.pre-commit-config.yaml`_ at the top level directory of this project.

.. _GitHub: https://github.com/savannahghi/idr-client
.. _pre-commit: https://pre-commit.com/
.. _.pre-commit-config.yaml: https://github.com/savannahghi/idr-client/blob/develop/.pre-commit-config.yaml
