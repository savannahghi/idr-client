# IDR Client

IDR(Integrated Data Repository) Client is a tool that extracts data from a
source(most likely a database), performs any transformations that may be required
on the data and then transmits it to a remote
[server](https://github.com/savannahghi/idr-server) for further processing and
consumption. The tool is authored in Python(3.8+) but working executable binaries
for Linux can be found on the [release section](https://github.com/savannahghi/idr-client/releases).

 [![Coverage Status](https://coveralls.io/repos/github/savannahghi/idr-client/badge.svg?branch=develop)](https://coveralls.io/github/savannahghi/idr-client?branch=develop)
 [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
 [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Getting Started
To run the app locally, you can download the latest executable binary from the
[release section](https://github.com/savannahghi/idr-client/releases) if you
have a Linux box. Note that the binary has only been tested on the following
Linux distros: Ubuntu 16.04 LTS, Ubuntu 18.04 LTS, Ubuntu 20.04 LTS and
Fedora 36. Compatibility for other Linux distros might be possible but is not
guaranteed. Users of other platforms can also clone this repo and set up the
project on their computers but this much more involving. Both of these set up
methods are described below as well as how to build an executable binary for
other platforms.

#### 1. Using the Executable Binary
This is by far the easiest way to set up and run the application and can be
achieved using the following steps:
1. Download the binary from the latest release:-
   ```bash
   curl https://github.com/savannahghi/idr-client/releases/download/v0.1.0/idr_client --output idr_client -L
   ```
2. Make the downloaded binary executable:-
   ```bash
   chmod u+x idr_client
   ```
3. Define a configuration file for the app to use. A template for the config
   file is provided with the tool, check the `.config.template.yaml` file and
   edit it to match your setup/needs.
4. Once you are done with the config file, you can run the app as follows:-
   ```bash
   idr_client -c /path/to/your/config.yaml
   ```
   Replace `/path/to/your/config.yaml` with the correct path to your config file.

   You are now good to go :thumbsup:.

#### 2. Cloning the Repo.
For this method, you will need have [Python 3.8.0](https://www.python.org/downloads/release/python-380/)
(3.10 is recommended) or above installed. You could optionally create a
[virtualenv](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)
for the project separate from the system Python. Next, perform the following
steps:
1. Clone this repository (if you haven't already) and CD into the root project
   directory, that is, the directory containing `pyproject.toml`. Unless
   otherwise specified, this is the directory we are going to run all the rest
   of the commands from.
2. Install the project's dependencies by running:-
   ```bash
    pip install -r requirements/base.txt
   ```
3. Define a configuration file for the app to use. A template for the config
   file is provided with the tool, check the `.config.template.yaml` file and
   edit it to match your setup/needs.
4. Once you are done with the config file, you can run the app as follows:-
   ```bash
   python -m app -c /path/to/your/config.yaml
   ```
   Replace /path/to/your/config.yaml with the correct path to your config file.

   That's it, you are now good to go :thumbsup:.

#### 3. Create an Executable Binary *(Optional)*
For those wishing to create executable binaries for other platforms, you will
need to follow most of method2's steps but with the following differences:

On step 2, install the project dependencies by running:-
```bash
pip install -r requirements/dev.txt
```

And then create the binary using the following command:-
```bash
pyinstaller app/__main__.py  --hidden-import apps/imp --collect-all app --name idr_client_temp -F
```
This will create an executable but the executable will still depend on the
target system/computer having the correct system libraries. More details on this
can be found [here](https://github.com/pyinstaller/pyinstaller/wiki/FAQ#gnulinux).
To learn more about the `pyinstaller` command, check the docs [here](https://pyinstaller.org).

To create a fully statically linked executable, run the following command:-
```bash
staticx dist/idr_client_temp dist/idr_client
```
The executable binary can be found on the `dist` directory of the project. To
learn more about the `staticx` command, check the docs [here](https://staticx.readthedocs.io).


## Concepts
This section is for the curious and those wishing to contribute. It provides a
summary description of how the app works and the concepts and terms used in the
project. These are:
* __Data Source Type__ - A data source type is just that, it describes a kind
  of data source together with the operations that can be performed around those
  data sources. Each data source type can have multiple *data sources*.
* __Data Source__ - A data source represents an entity that contains data of
  interest such as a database or a file. Each data source has multiple
  *extra metadata*.
* __Extract Metadata__ - This a description of the data to be extracted from a
  data source. An extract metadata also defines how data is extracted from a
  data source.
* __Upload Metadata__ - This describes data that has been extracted and how
  it's packaged for uploading to the remote server. Each upload metadata is
  always associated with a given *extract metadata*.

## License

[MIT License](https://github.com/savannahghi/idr-client/blob/develop/LICENSE)

Copyright (c) 2022, Savannah Informatics Global Health Institute
