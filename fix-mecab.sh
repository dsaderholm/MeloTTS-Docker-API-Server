#!/bin/bash
# MeCab fix script - run this inside the container if MeCab fails

echo "Fixing MeCab configuration..."

# Create the missing directory and config file
mkdir -p /usr/local/lib/python3.10/site-packages/unidic/dicdir
echo "dicdir = /var/lib/mecab/dic/debian" > /usr/local/lib/python3.10/site-packages/unidic/dicdir/mecabrc

# Alternative: point to system MeCab dictionary
echo "dicdir = /usr/share/mecab/dic/debian" > /usr/local/lib/python3.10/site-packages/unidic/dicdir/mecabrc

# Test MeCab
python3 -c "import MeCab; print('MeCab working:', MeCab.Tagger().parse('test'))"

echo "MeCab fix completed"
