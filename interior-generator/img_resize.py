from PIL import Image
import os

def resize_image(image_path, output_path, max_size):
    with Image.open(image_path) as img:
        img.thumbnail((max_size, max_size))
        img.save(output_path)

def resize_images_in_folder(folder_path, max_size=900):
    if not os.path.exists(folder_path):
        print(f"The folder {folder_path} does not exist.")
        return

    output_folder = os.path.join(folder_path, 'resized')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            try:
                resize_image(file_path, os.path.join(output_folder, filename), max_size)
                print(f"Resized and saved: {filename}")
            except Exception as e:
                print(f"Could not resize {filename}: {e}")

folder_path = '/Users/timdalxx/2024/zerodeling/backend/interior-generator/stabledesign/data/general_room/open_test'  # 여기에 폴더 경로를 입력하세요.
resize_images_in_folder(folder_path)
