from mpi4py import MPI
import cv2
import numpy as np
from pwn import *

def process_image_part(part, operation):
    if operation == 49:
        part = cv2.Canny(part, 100, 200)
    elif operation == 50:
        part = cv2.bitwise_not(part)
    elif operation == 51:
        part = cv2.medianBlur(part, 11)
    elif operation == 52:
        part = cv2.cvtColor(part, cv2.COLOR_BGR2GRAY)
        _, part = cv2.threshold(part, 128, 255, cv2.THRESH_BINARY)
    else:
        raise ValueError("Invalid Operation")
    return part

def split_image(image, num_splits):
    height = image.shape[0]
    split_height = height // num_splits
    return [image[i * split_height:(i + 1) * split_height] for i in range(num_splits)]

def combine_image(parts):
    return np.vstack(parts)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if size != 3:
    raise ValueError("This script requires exactly 3 MPI processes")

if rank == 0:
    # Master process
    print("Waiting for a connection...")

    l = listen(5000)
    recvd = l.clean(1)

    if recvd:
        with open('image.jpg', "wb") as file:
            file.write(recvd[0:len(recvd)-2])
        operation = recvd[len(recvd)-1]
        print(f"Operation: {operation}")

        img = cv2.imread('image.jpg')
        if img is None:
            print("Failed to read the image.")
            MPI.COMM_WORLD.Abort()
        print("Image received")

        # Split the image into parts
        parts = split_image(img, 2)

        # Send parts to workers
        comm.send(parts[0], dest=1, tag=1)
        comm.send(parts[1], dest=2, tag=2)
        comm.send(operation, dest=1, tag=3)
        comm.send(operation, dest=2, tag=4)

        # Receive processed parts from workers
        processed_part1 = comm.recv(source=1, tag=5)
        processed_part2 = comm.recv(source=2, tag=6)

        # Combine processed parts
        result_img = combine_image([processed_part1, processed_part2])
        print("Image edited")

        # Save the processed image
        cv2.imwrite('Result_image.jpg', result_img)

        with open('Result_image.jpg', 'rb') as file2:
            image2 = file2.read()
        l.send(image2)

        print("Image Sent")
    else:
        print("Failed to receive data from the client.")
        MPI.COMM_WORLD.Abort()

else:
    # Worker processes
    part = comm.recv(source=0, tag=rank)
    operation = comm.recv(source=0, tag=rank + 2)

    processed_part = process_image_part(part, operation)

    comm.send(processed_part, dest=0, tag=rank + 4)
