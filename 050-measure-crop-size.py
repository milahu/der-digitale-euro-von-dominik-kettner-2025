"""
Config for 060-rotate-crop-level.py
"""

scan_format = "tiff"

# --- Rotation settings ---
do_rotate = False
rotate_odd = 90
rotate_even = 270

# --- Crop settings ---
do_crop = False
crop_size = (1580, 2480)
crop_x = 168
# x1, y1, x2, y2 = crop_box
crop_odd_box = (crop_x, 0, crop_x + crop_size[0], crop_size[1])
crop_even_box = (0, 0, crop_size[0], crop_size[1])

# --- Level / brightness normalization ---
do_level = True

# lowthresh = 0.2 is too dark for the book cover -> use 0.1
# lowthresh = 0.1 # about 25/255 in GIMP
lowthresh = 0.2 # about 50/255 in GIMP
highthresh = 0.9 # about 230/255 in GIMP
# level = f"{lowthresh}x{highthresh}%"
