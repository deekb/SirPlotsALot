#!/usr/bin/bash

for file in ./*.svg; do convert -density 1200 -background none $file \( -clone 0 -fill white -colorize 100 \) -resize 64x64  `basename $file .svg`.png; done
