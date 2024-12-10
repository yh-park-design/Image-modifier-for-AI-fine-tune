import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image
import zipfile
import shutil

def process_images(input_files, output_dir, resolution, output_format, orientation, color_mode):
    for file in input_files:
        try:
            img = Image.open(file).convert("L")  # Convert to grayscale by default

            base_name = os.path.basename(file)
            name, ext = os.path.splitext(base_name)

            if color_mode == "grayscale":
                name += "_greyscale"
            elif color_mode == "black_and_white":
                img = img.point(lambda x: 255 if x > 128 else 0, "1")  # Convert to black and white
                name += "_bw"

            # Handle resolution transformations
            if resolution == "512x512_max":
                width, height = img.size
                if width > height:
                    new_width = 512
                    new_height = int((512 / width) * height)
                else:
                    new_height = 512
                    new_width = int((512 / height) * width)
                img = img.resize((new_width, new_height))
                name += "_max512"

            elif resolution == "512x512_min":
                width, height = img.size
                if width < height:
                    new_width = 512
                    new_height = int((512 / width) * height)
                else:
                    new_height = 512
                    new_width = int((512 / height) * width)
                img = img.resize((new_width, new_height))
                name += "_min512"

            # Handle orientation transformations
            if orientation == "90":
                img = img.rotate(-90, expand=True)
                name += "_90d"
            elif orientation == "180":
                img = img.rotate(180, expand=True)
                name += "_180d"
            elif orientation == "270":
                img = img.rotate(-270, expand=True)
                name += "_270d"

            # Set the output file extension
            if output_format == "original":
                ext = ext.lower()  # Keep original extension
            else:
                ext = f".{output_format.lower()}"

            output_path = os.path.join(output_dir, f"{name}{ext}")

            # Check if file exists and ask for overwrite
            if os.path.exists(output_path):
                overwrite = messagebox.askyesno("File Exists", f"The file '{output_path}' already exists. Do you want to overwrite it?")
                if not overwrite:
                    print(f"Skipped: {output_path}")
                    continue

            img.save(output_path)
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f"Failed to process {file}: {e}")

def extract_zip(file_path, extract_dir):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    return [os.path.join(extract_dir, file) for file in zip_ref.namelist() if file.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'))]

class GrayscaleTransformerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Transformer")
        self.input_files = []
        self.output_dir = ""
        self.resolution = "Original"
        self.output_format = "original"
        self.orientation = "0"
        self.color_mode = "grayscale"

        # Interface elements
        self.import_button = tk.Button(root, text="Import Images/ZIP", command=self.import_files)
        self.import_button.pack(pady=5)

        self.output_button = tk.Button(root, text="Select Export Location", command=self.select_output_location)
        self.output_button.pack(pady=5)

        self.color_mode_frame = tk.Frame(root)
        self.color_mode_frame.pack(pady=10)

        self.color_mode_label = tk.Label(self.color_mode_frame, text="Select Color Mode:")
        self.color_mode_label.pack(anchor="w")

        self.color_mode_checks = {}
        for mode_option, mode_value in [("Grayscale", "grayscale"), ("Black and White", "black_and_white")]:
            self.color_mode_checks[mode_value] = tk.Checkbutton(
                self.color_mode_frame, text=mode_option, command=lambda m=mode_value: self.set_color_mode(m))
            self.color_mode_checks[mode_value].pack(anchor="w")

        self.resolution_frame = tk.Frame(root)
        self.resolution_frame.pack(pady=10)

        self.original_resolution_check = tk.Checkbutton(
            self.resolution_frame, text="Original Resolution", command=self.set_original_resolution)
        self.original_resolution_check.pack(side=tk.LEFT, padx=10)

        self.resize_512_max_check = tk.Checkbutton(
            self.resolution_frame, text="Reduce Max Dimension to 512px", command=self.set_resize_512_max)
        self.resize_512_max_check.pack(side=tk.LEFT, padx=10)

        self.resize_512_min_check = tk.Checkbutton(
            self.resolution_frame, text="Reduce Min Dimension to 512px", command=self.set_resize_512_min)
        self.resize_512_min_check.pack(side=tk.RIGHT, padx=10)

        self.format_frame = tk.Frame(root)
        self.format_frame.pack(pady=10)

        self.format_label = tk.Label(self.format_frame, text="Select Output Format:")
        self.format_label.pack(anchor="w")

        self.format_checks = {}
        for format_option in ["original", "png", "jpg", "bmp", "tiff", "webp"]:
            self.format_checks[format_option] = tk.Checkbutton(
                self.format_frame, text=format_option.upper(), command=lambda f=format_option: self.set_output_format(f))
            self.format_checks[format_option].pack(anchor="w")

        self.orientation_frame = tk.Frame(root)
        self.orientation_frame.pack(pady=10)

        self.orientation_label = tk.Label(self.orientation_frame, text="Select Orientation:")
        self.orientation_label.pack(anchor="w")

        self.orientation_checks = {}
        for orientation_option in [("Original (0°)", "0"), ("90°", "90"), ("180°", "180"), ("270°", "270")]:
            self.orientation_checks[orientation_option[1]] = tk.Checkbutton(
                self.orientation_frame, text=orientation_option[0], command=lambda o=orientation_option[1]: self.set_orientation(o))
            self.orientation_checks[orientation_option[1]].pack(anchor="w")

        self.transform_button = tk.Button(root, text="Transform", command=self.transform_images, state=tk.DISABLED)
        self.transform_button.pack(pady=5)

        self.status_label = tk.Label(root, text="Status: Waiting for input", fg="blue")
        self.status_label.pack(pady=5)

        # Set default selections
        self.color_mode_checks["grayscale"].select()
        self.format_checks["original"].select()
        self.orientation_checks["0"].select()

    def import_files(self):
        file_types = [("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"), ("ZIP files", "*.zip")]
        files = filedialog.askopenfilenames(filetypes=file_types)
        if files:
            self.input_files = list(files)
            self.status_label.config(text=f"Imported {len(self.input_files)} files.", fg="green")
            self.transform_button.config(state=tk.NORMAL)

    def select_output_location(self):
        output_dir = filedialog.askdirectory()
        if output_dir:
            self.output_dir = output_dir
            self.status_label.config(text=f"Export location set to: {self.output_dir}", fg="green")

    def set_color_mode(self, selection):
        self.color_mode = selection
        self.deselect_other_checks(self.color_mode_checks[selection], self.color_mode_frame)
        self.status_label.config(text=f"Color mode set to: {selection.capitalize()}", fg="green")

    def set_original_resolution(self):
        self.resolution = "Original"
        self.deselect_other_checks(self.original_resolution_check, self.resolution_frame)
        self.status_label.config(text="Resolution set to Original", fg="green")

    def set_resize_512_max(self):
        self.resolution = "512x512_max"
        self.deselect_other_checks(self.resize_512_max_check, self.resolution_frame)
        self.status_label.config(text="Resolution set to reduce max dimension to 512px", fg="green")

    def set_resize_512_min(self):
        self.resolution = "512x512_min"
        self.deselect_other_checks(self.resize_512_min_check, self.resolution_frame)
        self.status_label.config(text="Resolution set to reduce min dimension to 512px", fg="green")

    def set_output_format(self, selection):
        self.output_format = selection
        self.deselect_other_checks(self.format_checks[selection], self.format_frame)
        self.status_label.config(text=f"Output format set to: {self.output_format.upper()}", fg="green")

    def set_orientation(self, selection):
        self.orientation = selection
        self.deselect_other_checks(self.orientation_checks[selection], self.orientation_frame)
        self.status_label.config(text=f"Orientation set to: {selection}°", fg="green")

    def deselect_other_checks(self, current_check, frame):
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Checkbutton) and widget != current_check:
                widget.deselect()

    def transform_images(self):
        if not self.output_dir:
            messagebox.showerror("Error", "Please select an export location.")
            return

        extracted_dir = None
        final_files = []

        for file in self.input_files:
            if file.lower().endswith('.zip'):
                extracted_dir = os.path.join(self.output_dir, "extracted_temp")
                os.makedirs(extracted_dir, exist_ok=True)
                extracted_files = extract_zip(file, extracted_dir)
                final_files.extend(extracted_files)
            else:
                final_files.append(file)

        process_images(final_files, self.output_dir, self.resolution, self.output_format, self.orientation, self.color_mode)

        if extracted_dir:
            shutil.rmtree(extracted_dir)  # Clean up temporary extracted files

        self.status_label.config(text=f"Transformation complete. Saved to: {self.output_dir}", fg="blue")
        messagebox.showinfo("Success", f"All images transformed and saved to: {self.output_dir}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GrayscaleTransformerApp(root)
    root.mainloop()