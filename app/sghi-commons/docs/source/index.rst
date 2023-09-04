.. sghi-commons documentation master file, created by
   sphinx-quickstart on Thu Aug  3 01:28:14 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: images/sghi_logo.webp
   :align: center

SGHI Commons
============

sghi-commons is a collection of reusable components and utilities used
throughout `SavannahGHI Python projects <sghi_github_py_projects_>`_.
They include utilities such as:

- Classes for creating application configuration.
- Classes for creating application registry.
- A dispatcher tool inspired by Django dispatch.

Installation
------------

We recommend using the latest version of Python. Python 3.10 and newer is
supported. We also recommend using a `virtual environment`_ in order
to isolate your project dependencies from other projects and the system.

Install the latest sghi-commons version using pip:

.. code-block:: bash

    pip install sghi-commons


API Reference
-------------

.. autosummary::
   :template: module.rst
   :toctree: api
   :caption: API
   :recursive:

     sghi.app
     sghi.config
     sghi.dispatch
     sghi.disposable
     sghi.exceptions
     sghi.registry
     sghi.tasks
     sghi.utils


.. _sghi_github_py_projects: https://github.com/savannahghi/?q=&type=all&language=python&sort=
.. _virtual environment: https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments
