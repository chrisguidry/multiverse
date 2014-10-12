#!/usr/bin/env python
#coding: utf-8
import os
import mimetypes
import urllib.parse
import zipfile

from flask import Flask, render_template, abort
import rarfile


app = Flask(__name__)
app.config.from_object('configuration')

mimetypes.add_type('application/x-cbr', '.cbr')
mimetypes.add_type('application/x-cbz', '.cbz')

ARCHIVE_TYPES = {
    'application/x-cbr': rarfile.RarFile,
    'application/x-cbz': zipfile.ZipFile
}
WEB_IMAGE_TYPES = {'image/png', 'image/jpeg'}

def open_archive(full_path):
    mimetype, _ = mimetypes.guess_type(full_path)
    return ARCHIVE_TYPES[mimetype](full_path)

def archive_list(archive):
    for entry in archive.infolist():
        if getattr(entry, 'isdir', lambda: False)():
            continue
        yield entry.filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/library/<path:path>/pages')
def pages(path):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if not os.path.isfile(full_path):
        abort(404)

    with open_archive(full_path) as archive:
        uris = ['/library/%s/pages/%s' % (path, member) for member in sorted(archive_list(archive))]
        return '\n'.join(uris), 200, {'Content-Type': 'text/plain'}

@app.route('/library/<path:path>/pages/<path:page>')
def page(path, page):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if not os.path.isfile(full_path):
        abort(404)

    with open_archive(full_path) as archive:
        return archive.read(page), 200, {'Content-Type': mimetypes.guess_type(page)[0]}

@app.route('/library/')
@app.route('/library/<path:path>')
def library(path=''):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if os.path.isdir(full_path):
        return series(full_path, path)
    elif os.path.isfile(full_path):
        return issue(full_path, path)
    abort(404)

def series(full_path, library_path):
    series = []
    issues = []
    for entry in os.listdir(full_path):
        if entry.startswith('.'):
            continue

        entry_full_path = os.path.join(full_path, entry)
        entry_uri = '/library/' + os.path.relpath(entry_full_path, app.config['LIBRARY_ROOT'])
        if os.path.isdir(entry_full_path):
            series.append(entry_uri)
        elif os.path.isfile(entry_full_path):
            issues.append(entry_uri)

    context = {
        'title': library_path,
        'series': series,
        'issues': issues
    }
    return render_template('series.html', **context)

def issue(full_path, library_path):
    series_path, archive_name = os.path.split(full_path)
    with open_archive(full_path) as archive:
        context = {
            'title': archive_name,
            'pages': [urllib.parse.quote('/library/%s/pages/%s' % (library_path, member))
                      for member in sorted(archive_list(archive))
                      if mimetypes.guess_type(member)[0] in WEB_IMAGE_TYPES]
        }
    return render_template('comic.html', **context)

if __name__ == '__main__':
    app.run()
