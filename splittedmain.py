import tkinter as tk
from tkinter import filedialog
import cv2  # OpenCV for image processing
import threading
import queue
from PIL import Image, ImageTk  # Pillow for image handling
from mpi4py import MPI  # MPI for distributed computing
from pwn import *

image_path = None
task_queue = queue.Queue()


class WorkerThread(threading.Thread):
    def __init__(self, task_queue):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.processed_image = None  # Attribute to store processed image

    def run(self):
        while True:
            task = self.task_queue.get()
            if task is None:
                break
            image, operation = task
            result = self.process_image(image, operation)
            self.processed_image = result  # Store the processed image
            # Notify GUI to update the displayed image
            app.update_displayed_image(result)

# 49 is edge detection
# 50 is color inversion
# 51 is BLUR
# 52 is Binarization


    def process_image(self, path, operation_var):
        conn = remote('102.37.138.221',5000)
        file = open(path,'rb')
        image = file.read()
        if operation_var == 'edge_detection':
            image = image + b"1"
            conn.send(image)
        elif operation_var == 'color_inversion':
            image = image + b"2"
            conn.send(image)
        elif operation_var == 'Blur':
            image = image + b"3"
            conn.send(image)
        elif operation_var == 'Binarization':
            image = image + b"4"
            conn.send(image)

        file2 = open('x.jpg','wb')
        x = conn.recvall()
        file2.write(x)
        result = cv2.imread('x.jpg', cv2.IMREAD_COLOR)
        conn.close()
        resized_result = cv2.resize(result, (500, 500))
        return resized_result  


class GUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Processor")
        self.geometry("700x700")

        self.image_path = None

        # Load the background image
        background_img = Image.open("Background.png")
        self.background_img = ImageTk.PhotoImage(background_img)
        
        # Create a label to display the background image
        self.background_label = tk.Label(self, image=self.background_img)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.image_label = tk.Label()
        self.image_label.pack()

        self.operation_var = tk.StringVar()
        self.operation_var.set("edge_detection")
        self.operation_menu = tk.OptionMenu(self, self.operation_var, "edge_detection", "color_inversion" ,  "Blur" , "Binarization")
        self.operation_menu.pack(side=tk.BOTTOM)

        self.download_button = tk.Button(self, text="Download Image", command=self.download_image, state=tk.DISABLED)
        self.download_button.pack(side=tk.BOTTOM)

        self.process_button = tk.Button(self, text="Process Image", command=self.process_image)
        self.process_button.pack(side=tk.BOTTOM)

        self.upload_button = tk.Button(self, text="Upload Image", command=self.upload_image)
        self.upload_button.pack(side=tk.BOTTOM)

        self.worker_thread = WorkerThread(task_queue)
        self.worker_thread.start()

    def upload_image(self):
        global image_path
        file_path = filedialog.askopenfilename()
        if file_path:
            image_path = file_path
            self.process_button.config(state=tk.NORMAL)
            self.download_button.config(state=tk.NORMAL)
            # Display the uploaded image
            self.display_uploaded_image(image_path)

    def process_image(self):
        global image_path
        if image_path:
            task_queue.put((image_path, self.operation_var.get()))  # Enqueue the processing task

            processed_image = self.worker_thread.processed_image
            if processed_image is not None:
                self.update_displayed_image(processed_image)

    def update_displayed_image(self, processed_image):
        processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
        processed_image = cv2.resize(processed_image, (500, 500))  
        img = Image.fromarray(processed_image)  # Convert processed image to PIL format
        img = ImageTk.PhotoImage(img)
        self.image_label.config(image=img)
        self.image_label.image = img  # Keep a reference to avoid garbage collection


    def display_uploaded_image(self, image_path):
        img = cv2.imread(image_path)
        img = cv2.resize(img, (500, 500))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.image_label.config(image=img)
        self.image_label.image = img  # Keep a reference to avoid garbage colle

    def download_image(self):
        global image_path
        if image_path:
            save_path = filedialog.asksaveasfilename(defaultextension=".png")
            if save_path:
                cv2.imwrite(save_path, self.worker_thread.processed_image)


if __name__ == "__main__":
    app = GUI()
    app.mainloop()
