import cv2
import numpy as np
from pwn import *

print("Waiting for a connection...")

l = listen(5000)
recvd = l.clean(1)

file = open('image.jpg',"wb")
file.write(recvd[0:len(recvd)-2])
operation = recvd[len(recvd)-1]
print(operation)


img = cv2.imread('image.jpg')

print("Image received")

# 49 is edge detection
# 50 is color inversion
# 51 is BLUR
# 52 is Binarization


if operation == 49:
    img = cv2.Canny(img,100,200)

elif operation == 50:
    img = cv2.bitwise_not(img)

elif operation == 51:
    img = cv2.medianBlur(img,11)

elif operation == 52:
# Apply thresholding
    img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    _, img = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
else:
    print("Invalid Operation")

print("Image edited")
# Save the thresholded image
cv2.imwrite('Result_image.jpg', img)



file2 = open('Result_image.jpg','rb')
image2 = file2.read()
l.send(image2)

print("Image Sent")