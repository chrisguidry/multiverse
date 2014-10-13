#coding:utf-8
"""A port of Ned Batchelder's quick, dirty, and inspired
PDF JPEG extraction code, updated for Python 3 and wrapped
in an interface compatible with zipfile and rarfile.

http://nedbatchelder.com/blog/200712/extracting_jpgs_from_pdfs.html
"""
from collections import OrderedDict

class PDFInfo(object):
    def __init__(self, pdffile, filename, startbyte, endbyte):
        self.pdffile = pdffile
        self.filename = filename
        self.startbyte = startbyte
        self.endbyte = endbyte
        self.CRC = startbyte

class PDFFile(object):
    def __init__(self, filename, mode='r'):
        self.filename = filename
        self.mode = mode
        self.pdf = None
        self.pages = None

    def __enter__(self):
        self.pdf = open(self.filename, self.mode + 'b')
        return self

    def __exit__(self, *args):
        self.pdf.close()
        self.pdf = None

    def infolist(self):
        self.cache_entries()
        return self.pages.values()

    def getinfo(self, page_name):
        self.cache_entries()
        return self.pages[page_name]

    def read(self, page_name):
        self.cache_entries()
        entry = self.pages[page_name]
        self.pdf.seek(entry.startbyte)
        return self.pdf.read(entry.endbyte - entry.startbyte)

    def cache_entries(self):
        if self.pages is not None:
            return

        self.pages = OrderedDict()
        for info in self.scan():
            self.pages[info.filename] = info

    def scan(self):
        pdf = self.pdf.read()

        startmark = b'\xff\xd8'
        startfix = 0
        endmark = b'\xff\xd9'
        endfix = 2
        i = 0

        njpg = 0
        while True:
            istream = pdf.find(b'stream', i)
            if istream < 0:
                break
            istart = pdf.find(startmark, istream, istream+20)
            if istart < 0:
                i = istream+20
                continue

            iend = pdf.find(b'endstream', istart)
            if iend < 0:
                raise Exception('Did not find end of stream!')
            iend = pdf.find(endmark, iend-20)
            if iend < 0:
                raise Exception('Did not find end of JPG!')

            istart += startfix
            iend += endfix
            yield PDFInfo(self, 'page%4d.jpg' % njpg, istart, iend)

            njpg += 1
            i = iend
