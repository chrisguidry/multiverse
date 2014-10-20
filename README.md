multiverse, a self-hosted comic reader
======================================

Requires Python 3.4.  Installation will install [Flask (0.10.1)](http://flask.pocoo.org/)
and [rarfile (2.6)](https://pypi.python.org/pypi/rarfile/2.2).

Includes the [Pure CSS library (0.5)](http://purecss.io/) and
[Google's Material Design icons (1.0)](https://github.com/google/material-design-icons/).


Basic Setup and Installation
============================

multiverse requires the `unrar` utility to open RAR files, including CBR
files.  On Mac OSX with homebrew, install with `brew install unrar`.

```
$ virtualenv --python=python3.4 --prompt='(multiverse)' .environment
$ ./environment/bin/pip install -r requirements.txt
$ cp configuration.py.example configuration.py
```

Edit `configuration.py` to your liking, importantly, setting `LIBRARY_ROOT`.

```
$ ./environment/bin/python multiverse.py
```

The default configuration sets `LIBRARY_ROOT` to the `./library` directory of
this repository; you may either alter that path to one of your choosing, or
you may use your operating system's facilities to mount another directory to
`./library`.  multiverse requires only read access to `LIBRARY_ROOT`.

