import cv2
import numpy as np
import pytesseract
import os

def solve(file_path):
    inputImage = cv2.imread(file_path)
    scl = 2.2
    resized = cv2.resize(inputImage, None, fx=scl, fy=scl, interpolation=cv2.INTER_AREA)
    im_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    thresh = 127
    im_bw = cv2.threshold(im_gray, thresh, 255, cv2.THRESH_BINARY)[1]

    # text = pytesseract.image_to_string(im_bw)
    # print(text)

    cv2.imshow('im_bw', im_bw)

    inverted = 255 - im_bw
    horizontal = np.copy(inverted)
    cv2.imshow('inverted', inverted)

    cols = horizontal.shape[1]
    horizontal_size = cols - 50
    # Create structure element for extracting horizontal lines through morphology operations
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    # Apply morphology operations
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)

    # Show extracted horizontal lines
    cv2.imshow('horizontal', horizontal)
    # Find the big contours/blobs on the filtered image:
    contours, hierarchy = cv2.findContours(horizontal, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # Store the poly approximation and bound
    contoursPoly = [None] * len(contours)

    # We need some dimensions of the original image:
    imageHeight = im_bw.shape[0]
    imageWidth = im_bw.shape[1]

    # Look for the outer bounding boxes:

    y_coords = []
    for i, c in enumerate(contours):

        # Approximate the contour to a polygon:
        contoursPoly = cv2.approxPolyDP(c, 3, True)

        # Convert the polygon to a bounding rectangle:
        boundRect = cv2.boundingRect(contoursPoly)

        # Get the bounding rect's data:
        [x,y,w,h] = boundRect

        # Calculate line middle (vertical) coordinate,
        # Start point and end point:
        lineCenter = y + h//2

        y_coords.append(lineCenter)

    y_coords.sort()
    prev_y = 0

    final_text = ''
    for y in y_coords:
        stat_line = im_bw[:, 10:-10][prev_y:y]
        cv2.imshow('stat_line' + str(y), stat_line)
        text = pytesseract.image_to_string(stat_line)
        final_text += text
        prev_y = y
        print(repr(text))

    # somehow is still unable to read when there are multiple lines I think, will try to isolate each line now
    # new_img = np.zeros((1, imageWidth))
    # for y in y_coords:
    #     new_img = np.append(new_img, im_bw[prev_y:y], axis=0)
    #     new_img = np.append(new_img, np.zeros((10, imageWidth)), axis=0)
    #     # new_img = np.append(new_img, np.ones((1, imageWidth)) * 255, axis=0)
    #     new_img = np.append(new_img, np.zeros((10, imageWidth)), axis=0)
    #     prev_y = y

    # # print(np.max(im_bw))

    # new_img = new_img[:, 5:-5].astype(np.uint8)

    # cv2.imshow('new_img', new_img)
    # # print(new_img)
    # # print(new_img.shape)

    # print('-'*100)
    # text2 = pytesseract.image_to_string(new_img)
    # print(text2)

    # trimmed_bw = im_bw[:, 5:-5]
    # print('-'*100)
    # text3 = pytesseract.image_to_string(trimmed_bw)
    # print(text3)

    if cv2.waitKey(0) and 0xff == ord('q'):
        cv2.destroyAllWindows()


mypath = os.getcwd() + '\ss'

files = []
for f in os.listdir(mypath):
    filepath = os.path.join(mypath, f)
    if os.path.isfile(filepath):
        files.append(filepath)

for filepath in files:
    solve(filepath)