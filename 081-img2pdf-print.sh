#!/usr/bin/env bash

set -eux

exec lp -o sides=two-sided-long-edge -o media=A4 -o print-quality=5 "$@" 080-img2pdf.pdf
