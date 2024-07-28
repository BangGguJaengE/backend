
import requests
from PIL import Image, ImageDraw
import re
from io import BytesIO

class ObjectDetection:
    @staticmethod
    def detect_objects(image_url, api_key):
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        body = {
            "requests": [
                {
                    "image": {
                        "source": {
                            "imageUri": image_url
                        }
                    },
                    "features": [
                        {
                            "type": "OBJECT_LOCALIZATION",
                            "maxResults": 20
                        }
                    ],
                    'imageContext': {
                        "languageHints": ["ko"]
                    }
                }
            ]
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            objects = response.json()['responses'][0]['localizedObjectAnnotations']
            img = ObjectDetection.fetch_image_from_url(image_url)
            if img is None:
                return None
            
            combined_results = []
            
            for obj in objects:
                box = obj['boundingPoly']['normalizedVertices']
                x_medi = (box[0]['x'] + box[2]['x']) / 2 * img.width
                y_medi = (box[0]['y'] + box[2]['y']) / 2 * img.height
                bbox = (
                    box[0]['x'] * img.width,
                    box[0]['y'] * img.height,
                    box[2]['x'] * img.width,
                    box[2]['y'] * img.height
                )
                cropped_image = img.crop(bbox)
                combined_results.append({
                    'label': obj['name'],
                    'coordinate': (x_medi, y_medi),
                    'bounding_box': bbox,
                    'image': cropped_image
                })
            
            return combined_results
        else:
            print("Error:", response.status_code, response.text)
            return None

    @staticmethod
    def fetch_image_from_url(image_url, resize_to=(512, 512)):
        response = requests.get(image_url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.resize(resize_to, Image.LANCZOS)
            return img
        else:
            print("Error fetching image:", response.status_code, response.text)
            return None
            
    @staticmethod
    def draw_boxes(image_url, combined_results, img_name):
        img = ObjectDetection.fetch_image_from_url(image_url)
        if img is None:
            return None
            
        draw = ImageDraw.Draw(img)

        for value in combined_results:
            bbox = value['bounding_box']
            draw.polygon([
                (bbox[0], bbox[1]),
                (bbox[2], bbox[1]),
                (bbox[2], bbox[3]),
                (bbox[0], bbox[3]),
            ], outline='red', width=5)

            draw.text((bbox[0], bbox[1]), value['label'], fill='red')

        match = re.search(r'([^/]+\.png)$', img_name)
        if match:
            filename = match.group(1)
        else:
            filename = "output.png"

        result_image_path = f"C:/취업준비/경진대회/새싹해커톤/이미지/{filename[:-4]}.png"
        
        img.save(result_image_path)
        # print(f"객체가 감지된 이미지를 '{result_image_path}'에 저장했습니다.")
        return result_image_path
