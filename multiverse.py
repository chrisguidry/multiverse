#!/usr/bin/env python
#coding: utf-8
import mimetypes
import os
import subprocess
import sys
import urllib.parse
import zipfile

from flask import Flask, abort, render_template, redirect, request, url_for
from flask.ext.assets import Environment, Bundle
import rarfile

import pdffile

app = Flask(__name__)
app.config.from_object('configuration')

assets = Environment(app)
assets.register('stylesheets', Bundle('third-party/pure-release-0.5.0/base-min.css',
                                      'third-party/pure-release-0.5.0/grids-min.css',
                                      'third-party/pure-release-0.5.0/grids-responsive-min.css',
                                      'styles.css',
                                      filters='cssmin' if not app.config['DEBUG'] else None,
                                      output='build/styles.css'))
assets.register('javascripts', Bundle('multiverse.js',
                                      filters='rjsmin' if not app.config['DEBUG'] else None,
                                      output='build/multiverse.js'))

mimetypes.add_type('application/x-cbr', '.cbr')
mimetypes.add_type('application/x-cbz', '.cbz')

ARCHIVE_TYPES = {
    'application/x-cbr': rarfile.RarFile,
    'application/x-cbz': zipfile.ZipFile,
    'application/pdf': pdffile.PDFFile
}
NOT_FOUND_EXCEPTIONS = (rarfile.NoRarEntry, KeyError)
WEB_IMAGE_TYPES = {'image/png', 'image/jpeg'}


forced_version = '-1'
_version = None
def code_version():
    global _version
    if not _version:
        _version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip().decode('utf-8') + forced_version
    return _version

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

def series_title(series_path):
    title, _ = os.path.splitext(os.path.basename(series_path))
    return title

def series_issues(series_path):
    for path, _, filenames in os.walk(series_path):
        for filename in filenames:
            if mimetypes.guess_type(filename)[0] not in ARCHIVE_TYPES:
                continue
            yield os.path.join(path, filename)

def next_issue(archive_path):
    series_path, archive_name = os.path.split(archive_path)
    for issue_path in series_issues(series_path):
        if issue_path > archive_path:
            return issue_path

def archive_page(archive, page):
    try:
        archive_info = archive.getinfo(page)
    except NOT_FOUND_EXCEPTIONS:
        abort(404)

    headers = {
        'Content-Type': mimetypes.guess_type(page)[0],
        'Cache-Control': 'private, max-age=%s' % (60*60*24*365),
        'ETag': str(archive_info.CRC)
    }

    if request.headers.get('If-None-Match') == headers['ETag']:
        return '', 304, headers
    return archive.read(page), 200, headers

@app.route('/library/<path:path>/pages/<path:page>')
def issue_page(path, page):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if not os.path.isfile(full_path):
        abort(404)

    with open_archive(full_path) as archive:
        return archive_page(archive, page)

@app.route('/manifest')
@app.route('/library/<path:path>/manifest')
def library_manifest(path=''):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if os.path.isdir(full_path):
        return series_manifest(full_path, path)
    elif os.path.isfile(full_path):
        return issue_manifest(full_path, path)
    abort(404)

def series_manifest(full_path, library_path):
    covers = []
    for filename in sorted(os.listdir(full_path)):
        entry_full_path = os.path.join(full_path, filename)
        if filename.startswith('.'):
            continue
        if os.path.isfile(entry_full_path) and mimetypes.guess_type(filename)[0] not in ARCHIVE_TYPES:
            continue
        covers.append(cover(entry_full_path))

    context = {
        'version': code_version(),
        'covers': covers
    }

    headers = {
        'Content-Type': 'text/cache-manifest',
        'Cache-Control': 'no-store'
    }
    return render_template('library.manifest', **context), 200, headers

def issue_manifest(full_path, library_path):
    with open_archive(full_path) as archive:
        context = {
            'version': code_version(),
            'pages': [
                url_for('issue_page', path=library_path, page=page)
                for page in archive_pages(archive)
            ]
        }

    headers = {
        'Content-Type': 'text/cache-manifest',
        'Cache-Control': 'no-store'
    }
    return render_template('issue.manifest', **context), 200, headers

def cover(path):
    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if os.path.isdir(full_path):
        return series_cover(full_path)
    elif os.path.isfile(full_path):
        return issue_cover(full_path)
    abort(404)

def series_cover(full_path):
    for archive_path in series_issues(full_path):
        try:
            return issue_cover(archive_path)
        except Exception as e:
            continue
    abort(404)

def issue_cover(full_path):
    with open_archive(full_path) as archive:
        try:
            cover = next(archive_pages(archive))
        except StopIteration:
            abort(404)
        else:
            relative_path = os.path.relpath(full_path, app.config['LIBRARY_ROOT'])
            return url_for('issue_page', path=relative_path, page=cover)

def url_of(path):
    return url_for('library', path=path) if path else url_for('index').strip('/')

def manifest_url(path):
    return url_for('manifest', path=path) if path else url_for('global_manifest').strip('/')

def paths_for(path):
    parts = path.split(os.sep)
    return [(path, url_for('library', path=os.path.join(*parts[:index+1]))) for
            index, path in enumerate(parts[:-1])]

@app.route('/')
def index():
    return library()

@app.route('/manifest')
def global_manifest():
    return manifest()

@app.route('/search')
def global_search():
    return search()

@app.route('/library/<path:path>/search')
def search(path=''):
    query = request.args.get('q')
    if not query:
        return redirect(url_for('library', path=path) if path else url_for('index'))

    full_path = os.path.join(app.config['LIBRARY_ROOT'], path)
    if not os.path.isdir(full_path):
        abort(404)

    query = query.lower().replace(' ', '')
    items = []
    for root_path, directories, filenames in os.walk(full_path):
        for collection in [directories, filenames]:
            for filename in collection:
                if query not in filename.lower().replace(' ', ''):
                    continue

                entry_full_path = os.path.join(root_path, filename)
                if mimetypes.guess_type(entry_full_path)[0] not in ARCHIVE_TYPES:
                    continue

                relative_path = os.path.relpath(entry_full_path, app.config['LIBRARY_ROOT'])
                items.append({
                    'uri': url_for('library', path=relative_path),
                    'title': archive_title(entry_full_path),
                    'cover': cover(entry_full_path)
                })

    context = {
        'title': 'results for "%s"' % query,
        'path': url_of(path),
        'paths': paths_for(path),
        'query': query,
        'items': items
    }
    return render_template('library.html', **context)

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
        entry_full_path = os.path.join(full_path, filename)
        if filename.startswith('.'):
            continue
        if os.path.isfile(entry_full_path) and mimetypes.guess_type(filename)[0] not in ARCHIVE_TYPES:
            continue

        relative_path = os.path.relpath(entry_full_path, app.config['LIBRARY_ROOT'])
        items.append({
            'uri': url_for('library', path=relative_path),
            'title': archive_title(entry_full_path),
            'cover': cover(entry_full_path)
        })

    context = {
        'title': series_title(full_path),
        'path': url_of(library_path),
        'manifest_url': manifest_url(path),
        'paths': paths_for(library_path),
        'items': items
    }
    return render_template('library.html', **context)

def issue(full_path, library_path):
    next_archive = next_issue(full_path)
    next = None
    if next_archive:
        next = {
            'uri': url_for('library', path=os.path.relpath(next_archive, app.config['LIBRARY_ROOT'])),
            'title': archive_title(next_archive),
            'cover': cover(next_archive)
        }

    with open_archive(full_path) as archive:
        context = {
            'title': archive_title(full_path),
            'manifest_url': manifest_url(path),
            'path': url_of(library_path),
            'paths': paths_for(library_path),
            'pages': [{
                'uri': url_for('issue_page', path=library_path, page=page),
                'filename': urllib.parse.quote(page)
            } for page in archive_pages(archive)],
            'next_issue': next
        }
    return render_template('reader.html', **context)


if __name__ == '__main__':
    bind_address, bind_port = None, None
    if len(sys.argv) == 2:
        if ':' in sys.argv[1]:
            bind_address, bind_port = sys.argv[1].split(':')
        else:
            bind_address = sys.argv[1]
    app.run(host=bind_address or '127.0.0.1', port=int(bind_port or 5000))
