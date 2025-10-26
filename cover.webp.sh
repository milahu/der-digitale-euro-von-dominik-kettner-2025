#!/bin/sh

# TODO set config values
cover_src=070-deskew/287.tiff

magick "$cover_src" -scale 50% -quality 10% cover.webp
