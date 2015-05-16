#coding: utf-8
import os

if os.environ.get('ENV') == 'development':
    DEBUG = True
    ASSETS_DEBUG = True
else:
    DEBUG = False
    ASSETS_DEBUG = False

LIBRARY_ROOT = '/library'
APPLICATION_ROOT = None # may be /multiverse, for example, if running in a subdirectory
