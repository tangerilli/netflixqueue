#!/bin/bash

rm -rf chrome/js chrome/css safari/netflixqueue.safariextension/*.css safari/netflixqueue.safariextension/*.js
# Need to copy rather than symlink because chrome apparently doesn't like symlinks
cp -Rp common/js chrome/js
cp -Rp common/css/ chrome/css

# cp `pwd`/common/css/*.css safari/netflixqueue.safariextension/
# cp `pwd`/common/js/*.js safari/netflixqueue.safariextension/

ln `pwd`/common/css/*.css safari/netflixqueue.safariextension/
ln `pwd`/common/js/*.js safari/netflixqueue.safariextension/