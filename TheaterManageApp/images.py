import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

root = tk.Tk()
root.title("Import Images")

image_label = tk.Label(root)
image_label.pack()

def open_image():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")]
    )
    
    if file_path: 
        
        image = Image.open(file_path)
        photo = ImageTk.PhotoImage(image)
        image_label.config(image=photo)
        image_label.image = photo
        
open_button = tk.Button(root, text="Open Image", command=open_image)
open_button.pack()

root.mainloop()
