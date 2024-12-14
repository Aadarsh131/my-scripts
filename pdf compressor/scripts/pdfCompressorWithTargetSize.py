import fitz  # PyMuPDF
from PIL import Image
import io
import os
import json
from matplotlib import pyplot as plt
from matplotlib.widgets import RectangleSelector

def select_crop_area(image_path):
    """
    Allows the user to interactively select a cropping area on an image.

    Parameters:
        image_path (str): Path to the image file.

    Returns:
        tuple: Cropping coordinates (left, top, right, bottom).
    """
    img = Image.open(image_path)
    fig, ax = plt.subplots()
    ax.imshow(img)

    coords = []

    def onselect(eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, yclick.ydata
        # Clamp the coordinates to the image boundaries
        left = max(0, min(x1, x2))
        top = max(0, min(y1, y2))
        right = min(img.width, max(x1, x2))
        bottom = min(img.height, max(y1, y2))
        coords.extend([left, top, right, bottom])
        plt.close()

    rect_selector = RectangleSelector(
        ax, onselect, drawtype='box', useblit=True, button=[1],
        minspanx=5, minspany=5, spancoords='pixels', interactive=True
    )
    plt.show()
    return tuple(int(c) for c in coords)

def save_crop_coords(file_path, crop_coords_list):
    """
    Save cropping coordinates to a JSON file.

    Parameters:
        file_path (str): Path to the JSON file.
        crop_coords_list (list): List of cropping coordinates.
    """
    with open(file_path, 'w') as file:
        json.dump(crop_coords_list, file)

def load_crop_coords(file_path):
    """
    Load cropping coordinates from a JSON file.

    Parameters:
        file_path (str): Path to the JSON file.

    Returns:
        list: List of cropping coordinates.
    """
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return None

def reduce_pdf_size(input_pdf, output_pdf, image_quality=18, dpi=165, crop_coords_list=None, enable_cropping=True):
    """
    Reduce the size of a scanned PDF by converting pages to grayscale, resizing, and compressing images.
    Optionally crops the images if cropping is enabled.

    Parameters:
        input_pdf (str): Path to the input PDF file.
        output_pdf (str): Path to save the reduced-size PDF.
        image_quality (int): Quality of the images (1-100, higher is better quality).
        dpi (int): Resolution for downsampling images.
        crop_coords_list (list of tuples): List of crop coordinates (left, top, right, bottom) for each page.
        enable_cropping (bool): If True, applies cropping based on crop_coords_list.
    """
    pdf_document = fitz.open(input_pdf)
    new_pdf = fitz.open()

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image_list = page.get_images(full=True)
        if not image_list:
            new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
            continue

        pix = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY)
        pil_image = Image.open(io.BytesIO(pix.tobytes(output="png")))

        if enable_cropping and crop_coords_list and page_num < len(crop_coords_list):
            left, top, right, bottom = crop_coords_list[page_num]
            left = max(0, left)
            top = max(0, top)
            right = min(pil_image.width, right)
            bottom = min(pil_image.height, bottom)
            pil_image = pil_image.crop((left, top, right, bottom))

        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=image_quality, optimize=True)
        buffer.seek(0)

        new_page = new_pdf.new_page(width=pil_image.width, height=pil_image.height)
        new_page.insert_image(
            fitz.Rect(0, 0, pil_image.width, pil_image.height),
            stream=buffer.read(),
            keep_proportion=True
        )

    new_pdf.save(output_pdf, deflate=True)
    new_pdf.close()
    pdf_document.close()

def reduce_pdf_to_target_size(input_pdf, output_pdf, target_size_mb, initial_quality=50, initial_dpi=160, crop_coords_list=None, enable_cropping=True):
    """
    Reduce PDF size to approximate target size by adjusting image quality and DPI.

    Parameters:
        input_pdf (str): Path to the input PDF file.
        output_pdf (str): Path to save the reduced PDF.
        target_size_mb (float): Desired output file size in MB.
        initial_quality (int): Starting image quality (1-100).
        initial_dpi (int): Starting DPI for images.
        crop_coords_list (list of tuples): Optional crop coordinates for each page.
        enable_cropping (bool): If True, enables cropping.
    """
    quality = initial_quality
    dpi = initial_dpi
    step_quality = 5
    step_dpi = 10

    for _ in range(10):  # Limit iterations to prevent infinite loops
        reduce_pdf_size(input_pdf, output_pdf, image_quality=quality, dpi=dpi, crop_coords_list=crop_coords_list, enable_cropping=enable_cropping)
        current_size_mb = os.path.getsize(output_pdf) / (1024 * 1024)

        if abs(current_size_mb - target_size_mb) < 0.1:  # Close enough to target size
            print(f"Target size achieved: {current_size_mb:.2f} MB")
            break

        if current_size_mb > target_size_mb:
            quality = max(10, quality - step_quality)  # Decrease quality
            if dpi > 160:
                dpi = max(160, dpi - step_dpi)  # Decrease DPI but not below 160
        else:
            quality = min(100, quality + step_quality)  # Increase quality
            dpi = min(300, dpi + step_dpi)  # Increase DPI

    print(f"Final size: {current_size_mb:.2f} MB with quality={quality} and dpi={dpi}")

if __name__ == "__main__":
    input_pdf = "/home/aadarsh/Downloads/1REducePDFSizeJiju/experience letter.pdf"
    output_pdf = "/home/aadarsh/Downloads/1REducePDFSizeJiju/experience letter_targeSize_compressed.pdf"
    target_size_mb = 0.95  # Desired output size in MB
    crop_coords_file = "crop_coords.json"
    enable_cropping = False  # Set True to enable cropping

    if not os.path.exists(input_pdf):
        print(f"Input file {input_pdf} not found.")
    else:
        crop_coords_list = load_crop_coords(crop_coords_file) if enable_cropping else None

        if enable_cropping and not crop_coords_list:
            crop_coords_list = []
            temp_image_folder = "temp_images"
            os.makedirs(temp_image_folder, exist_ok=True)

            pdf_document = fitz.open(input_pdf)
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                pix = page.get_pixmap(dpi=150)
                image_path = os.path.join(temp_image_folder, f"page_{page_num}.png")
                pix.save(image_path)
                print(f"Select crop area for page {page_num + 1}")
                coords = select_crop_area(image_path)
                crop_coords_list.append(coords)

            for file in os.listdir(temp_image_folder):
                os.remove(os.path.join(temp_image_folder, file))
            os.rmdir(temp_image_folder)

            save_crop_coords(crop_coords_file, crop_coords_list)

        reduce_pdf_to_target_size(input_pdf, output_pdf, target_size_mb, crop_coords_list=crop_coords_list, enable_cropping=enable_cropping)

