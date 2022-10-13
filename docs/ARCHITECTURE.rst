=======================
IDR Client Architecture
=======================

This document describes among other things the core concepts used through out
this project, the layout of the project and the class hierarchy of the main
domain models in the project. All these are important in order to understand
how the application is structured and how the different components of the
application fit together and interact with each other.


Concepts and Terminology
------------------------

This section contains important terms and concept central to the project.

Core Domain
~~~~~~~~~~~

The core domain of the project is majorly composed of the following components:

* **Data Source Type** - A data source type is just that, it describes a kind
  of data source together with the operations that can be performed around
  those data sources. Each data source type can have multiple *data sources*.
  As well as being a container for *data sources*, a data source type also
  exposes concrete implementations of the other core domain models that define
  properties and behaviours that are useful when working with data of the
  given *type*. This allows the application to work with data of different
  types and from different sources.
* **Data Source** - A data source represents an entity that contains data of
  interest such as a database or a file. Each data source has multiple
  *extract metadata* associated with it.
* **Extract Metadata** - This a description of the data to be extracted from a
  *data source*. These description can include *(but is not limited)*
  properties such as the scope, depth and amount of data to be extracted from a
  data source. An extract metadata also defines how data is extracted from it's
  parent *data source*.
* **Upload Metadata** - This describes the attributes of the extracted data and
  how it's packaged for uploading to the remote server. Each upload metadata is
  always associated with a given *extract metadata*. Note that an upload
  metadata doesn't contain the actual data to be uploaded, just information
  about the data. The actual data is contained by the *upload chunks*
  associated with the given upload metadata.
* **Upload Chunk** - Before data is uploaded to the server, it is partitioned
  into smaller units *(for transmission efficiency reasons)* which are referred
  to as upload chunks. These chunks are then uploaded to the server.

These domain components are defined in the ``app.core.domain`` module as
interfaces meant to be implemented for each *data source type* that the
application needs to support. The default implementations that ship with the
application can be found at the ``app.imp`` package. This is designed to
emulate something similar to the `Service Provider Interface <spi_>`_ pattern in
Java.

Transport
~~~~~~~~~

A transport in the project represents the flow of data to and from the IDR
Client. Specifically, a transport connects the IDR Client to a metadata source
and also connects the client to the final destination of the extracted data. If
it helps, a transport can be thought of as an interface composed of two other
interfaces, ``MetadataProvider`` and ``DataSink``. In the future, the transport
interface might as well be split into those two interfaces if the need arises
but for now it remains as a single interface. The application receives metadata
through a transport and uploads the final data using a transport. A transport
can be anything from a HTTP API to a filesystem API. The transport interface is
defined in the ``app.core.transport`` module whereas the ``app.lib.transports``
package contains common transport implementations.

Task
~~~~

A task is a job or an action that takes an input and returns an output. Most
actions and processes in the project are modelled by composing different tasks
to achieve the desired objective. The task interface is defined at the
``app.core.task`` module whereas the ``app.lib.tasks`` package provides most
common tasks implementations as well as tasks that can be used to compose
multiple tasks.

Project Layout
--------------

The project structure/layout.

::

    .
    idr-client
    ├── ...other project configuration files.
    ├── app - The root src directory.
    |   ├── core - The core application components.
    |   |   ├── domain.py - Interfaces describing the services and essential processes provided by the application.
    |   |   ├── exceptions.py - Defines key application errors and exception used through out the project.
    |   |   ├── mixins.py - Defines components and interfaces used to model common behaviours and reusable functionality.
    |   |   ├── serializers.py - Defines interfaces that convert python objects into simple native types for easy storage and/or transmission.
    |   |   ├── task.py - Defines the interface that models a job or piece of work in the application.
    |   |   └── transport.py - Defines an interface that models the flow of data to and from the application.
    |   |
    |   ├── imp - Implementations of the core services.
    |   |
    |   ├── lib - Utilities and helpers.
    |   |   ├── config - Classes and functions needed to configure the application.
    |   |   ├── tasks - Implementations of common utility tasks.
    |   |   ├── transports - Different implementations of the transport interface.
    |   |   ├── app_registry.py - Contains the implementation of the main application registry.
    |   |   ├── checkers.py - Defines validators used throughout the application.
    |   |   └── module_loading.py - Defines utilities used for dynamic module loading.
    |   |
    |   ├── use_cases - This are application specific operations.
    |   |   ├── fetch_metadata.py - Defines fetch metadata operations.
    |   |   ├── main_pipeline.py - The main application pipeline operations.
    |   |   ├── run_extraction.py - Define data extraction operations.
    |   |   ├── types.py - Defines common typings used within the use cases package.
    |   |   └── upload_extracts.py - Defines data upload operations.
    |   |
    |   ├── __init__.py - Defines the application setup operations.
    |   ├── __main__.py - The main application entry point.
    |   └── __version__.py - Metadata about the application.
    |
    ├── docs - Documentation for the project.
    |
    ├── logs - A directory that can be used to store log files during development. This is not needed to run the application but is there for convenience.
    |
    ├── requirements - Defines dependencies needed to by the application.
    |   ├── base.txt - The key dependencies needed for the application to run.
    |   ├── dev.txt - Dependencies needed to set up a development environment for the project.
    |   └── test.txt - Dependencies needed to test the application.
    |
    └── tests - Tests for the application.


.. _spi: https://docs.oracle.com/javase/tutorial/sound/SPI-intro.html
