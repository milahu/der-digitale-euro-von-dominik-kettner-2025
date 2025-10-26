#!/usr/bin/env python3

INPUT_DIR = "060-rotate-crop-level"
OUTPUT_DIR = "065-remove-page-borders"

# === Tuning parameters ===
BORDER_SIZE = 100  # pixels

"""
AI prompt:

create a python script to remove grey (or black) page borders from scanned images.
the pages are white with black text.
the pages are no perfect rectangles, rather crooked trapezes with crooked lines...
so the algorithm should "overcut" the pages:
it should cut at the inner-most page edge,
so where the page edge is further outside some white area from the page is removed.

the script should process an input directory with *.tiff images
and write output images to an output directory (same image format).
the input and output paths should be hard-coded in the script,
so the script takes no command-line arguments.
the script should be based on the PIL (pillow) image library
(and on the opencv and numpy libraries when necessary)

...
"""

import os
from PIL import Image
import numpy as np
import cv2

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect

def process_image(in_path, out_path):
    img = cv2.imread(in_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Invert if necessary, so the page is always "white" for thresholding
    # We'll use Otsu's method to detect high-contrast area
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Determine whether the page is darker or lighter than background
    mean_val = cv2.mean(gray, mask=None)[0]
    if mean_val < 127:  # dark page: invert mask
        mask = cv2.bitwise_not(mask)

    # Morphology to remove small gaps
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print(f"Warning: no contours found in {in_path}")
        return
    page_contour = max(contours, key=cv2.contourArea)

    # Approximate contour to quadrilateral
    epsilon = 0.02 * cv2.arcLength(page_contour, True)
    approx = cv2.approxPolyDP(page_contour, epsilon, True)
    if len(approx) != 4:
        approx = cv2.convexHull(page_contour)
        if len(approx) < 4:
            print(f"Warning: not enough points for perspective in {in_path}")
            return
        # pick 4 extreme points
        pts = np.array([
            approx[approx[:,0,0].argmin()][0],  # leftmost
            approx[approx[:,0,1].argmin()][0],  # topmost
            approx[approx[:,0,0].argmax()][0],  # rightmost
            approx[approx[:,0,1].argmax()][0]   # bottommost
        ])
    else:
        pts = approx.reshape(4,2)

    rect = order_points(pts)

    # Perspective transform
    widthA = np.linalg.norm(rect[2] - rect[3])
    widthB = np.linalg.norm(rect[1] - rect[0])
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(rect[1] - rect[2])
    heightB = np.linalg.norm(rect[0] - rect[3])
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    # # Add internal white border
    # h, w = warped.shape[:2]
    # canvas = np.ones_like(warped) * 255
    # b = BORDER_SIZE
    # canvas[b:h-b, b:w-b] = warped[b:h-b, b:w-b]

    h, w = warped.shape[:2]
    b = BORDER_SIZE

    # Prepare a canvas with the same content as warped
    canvas = warped.copy()

    # Function to compute average color along a strip
    def avg_color_strip(img, axis, start, end, strip_width=1):
        if axis == 'top':
            strip = img[start:end, :, :]
        elif axis == 'bottom':
            strip = img[h-end:h-start, :, :]
        elif axis == 'left':
            strip = img[:, start:end, :]
        elif axis == 'right':
            strip = img[:, w-end:w-start, :]
        else:
            raise ValueError("Invalid axis")
        return np.mean(strip, axis=(0,1)).astype(np.uint8)

    # Fill borders with local average color
    canvas[0:b, :, :] = avg_color_strip(canvas, 'top', 50, 100)       # top border
    canvas[h-b:h, :, :] = avg_color_strip(canvas, 'bottom', 50, 100)  # bottom border
    canvas[:, 0:b, :] = avg_color_strip(canvas, 'left', 50, 100)      # left border
    canvas[:, w-b:w, :] = avg_color_strip(canvas, 'right', 50, 100)   # right border

    print(f"writing {out_path}")
    cv2.imwrite(out_path, canvas)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = [f for f in sorted(os.listdir(INPUT_DIR)) if f.lower().endswith((".tif", ".tiff"))]
    if not files:
        print("No TIFF files found in", INPUT_DIR)
        return
    for f in files:
        # if f != "014.tiff" : continue # debug
        in_path = os.path.join(INPUT_DIR, f)
        out_path = os.path.join(OUTPUT_DIR, f)
        if os.path.exists(out_path): continue
        try:
            process_image(in_path, out_path)
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    main()
