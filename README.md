# gttabb

A python script to extract point of sales from GTT supplied PDF files, augments them
with their position and export them as a csv file.

PDF files downloaded from here:

http://www.gtt.to.it/urbana/rivenditori.shtml

Points extracted with this script are available on a map here:

https://xrmx.cartodb.com/viz/0c6e3b60-538d-11e4-a381-0e9d821ea90d/map

## How to use

Should work fine with cpython 2.7+, pypy > 2.4.0

```
pip install -r requirements.txt
python gttabb <google geocode api key> <pdf> [<pdf>]
```

## Notes

The whole process is quite slow. To speed things up you can give it a try to pypy:
on my laptop pypy is 4x faster than cpython during the *pdftables* part

The *pdftables* library is used to extract the table from the pdfs. Unfortunately it
is not developed anymore as free software. The *0.0.4* version available in *pypi*
is a crippled version of the one used in http://pdftables.com.
Various forks of an old version of the library are available in github. These versions
ship an infant *poppler* backend which is at least an order of magnitude faster than
than the *pdfminer* one. Unfortunately the various forks and especially the *poppler*
backend does not work ouf of the box.
