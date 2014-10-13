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
    return ARCHIVE_TYPES[mimetype](full_path, mode='r')

def archive_files(archive):
    for entry in archive.infolist():
        if getattr(entry, 'isdir', lambda: False)():
            continue
        yield entry.filename

def archive_pages(archive):
    return (member for member in sorted(archive_files(archive))
            if mimetypes.guess_type(member)[0] in WEB_IMAGE_TYPES)

def archive_title(archive_path):
    title, _ = os.path.splitext(os.path.basename(archive_path))
    return title

@app.route('/library/<path:path>/pages/<path:page>')
def issue_page(path, page):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if not os.path.isfile(full_path):
        abort(404)

    with open_archive(full_path) as archive:
        return archive.read(page), 200, {'Content-Type': mimetypes.guess_type(page)[0]}

@app.route('/library/<path:path>/cover')
def cover(path):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if os.path.isdir(full_path):
        return series_cover(full_path)
    elif os.path.isfile(full_path):
        return issue_cover(full_path)
    abort(404)

def series_cover(full_path):
    for path, _, filenames in os.walk(full_path):
        for filename in filenames:
            if mimetypes.guess_type(filename)[0] in ARCHIVE_TYPES:
                try:
                    return issue_cover(os.path.join(path, filename))
                except Exception:
                    continue
    abort(404)

def issue_cover(full_path):
    with open_archive(full_path) as archive:
        cover = next(archive_pages(archive))
        return archive.read(cover), 200, {'Content-Type': mimetypes.guess_type(cover)[0]}

@app.route('/')
@app.route('/library/<path:path>')
def library(path=''):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if os.path.isdir(full_path):
        return series(full_path, path)
    elif os.path.isfile(full_path):
        return issue(full_path, path)
    abort(404)

def series(full_path, library_path):
    items = []
    for filename in sorted(os.listdir(full_path)):
        if filename.startswith('.'):
            continue

        entry_full_path = os.path.join(full_path, filename)
        relative_path = os.path.relpath(entry_full_path, app.config['LIBRARY_ROOT'])
        items.append({
            'uri': '/library/' + urllib.parse.quote(relative_path),
            'title': archive_title(entry_full_path)
        })

    context = {
        'title': library_path,
        'items': items
    }
    return render_template('library.html', **context)

def issue(full_path, library_path):
    series_path, archive_name = os.path.split(full_path)
    with open_archive(full_path) as archive:
        context = {
            'title': archive_title(full_path),
            'pages': [{
                'uri': urllib.parse.quote('/library/%s/pages/%s' % (library_path, page)),
                'filename': urllib.parse.quote(page)
            } for page in archive_pages(archive)]
        }
    return render_template('reader.html', **context)


if __name__ == '__main__':
    app.run()
