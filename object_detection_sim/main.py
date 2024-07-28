
from skimage.metrics import structural_similarity as ssim
from PIL import Image, ImageDraw
import os
import numpy as np
from Objectdetection import *

class SimilarityChecker:
    
    @staticmethod
    def calculate_similarity(image1, image2):

        # Resize and convert images to grayscale

        image1 = image1.resize((512, 512)).convert('L')
        image2 = image2.resize((512, 512)).convert('L')

        # Convert images to numpy arrays

        image1 = np.array(image1, dtype=np.float32)
        image2 = np.array(image2, dtype=np.float32)

        # Compute SSIM and specify the data range

        similarity, _ = ssim(image1, image2, data_range=image1.max() - image1.min(), full=True)
        return similarity

    @staticmethod
    def find_most_similar_object(cropped_image, folder_path):
        highest_similarity = -1
        most_similar_image = None
        most_similar_label = None

        # Iterate through images in the folder
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            comparison_image = Image.open(file_path)

            # Calculate similarity
            similarity = SimilarityChecker.calculate_similarity(cropped_image, comparison_image)
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_similar_image = comparison_image
                most_similar_label = filename

        return most_similar_label, highest_similarity, most_similar_image

if __name__ == "__main__":
    # Object detection image
    # image_path = "C:/취업준비/경진대회/새싹해커톤/이미지/생성된이미지.png"  # 이미지 파일 경로 설정
    image_url = 'https://cdn.ggumim.co.kr/cache/star/600/20160703033324R0baDhy8yK.png'
    api_key = "AIzaSyAMhzr2qmLoBugV6tUCSN_MCz9BXQonAME"  # 발급받은 API 키 입력
    # Similarity check images
    folder_path = "C:/취업준비/경진대회/새싹해커톤/이미지/이미지사진"  # 비교할 이미지들이 있는 폴더 경로
    # Path to save the most similar images
    save_path = "C:/취업준비/경진대회/새싹해커톤/이미지/이미지사진_유사도"  # 유사한 이미지를 저장할 경로

    
    # Create the save path folder if it doesn't exist
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    try:
        combined_results = ObjectDetection.detect_objects(image_url, api_key)
        if combined_results:
            # for result in combined_results:
            #     print(result)
            print("객체 감지 성공했습니다.")
            result_image_path = ObjectDetection.draw_boxes(image_url, combined_results, image_url)
        else:
            print("객체를 인식하지 못했습니다.")
    except Exception as e:
        print(f"Error in main execution: {e}")
