from google.cloud import vision
from google.auth import load_credentials_from_file

# 이런식으로도 구성 가능. 이미지에서 텍스트 디텍션
"""
@router.post("/detect_text")
async def detect_text(file: UploadFile = File(...)):
    # 이미지 파일 읽기
    content = await file.read()

    # Vision 클라이언트 생성
    client = vision.ImageAnnotatorClient()

    # 이미지 객체 생성
    image = vision.Image(content=content)

    # 텍스트 인식 요청
    response = client.text_detection(image=image)
    texts = response.text_annotations

    # 결과 반환
    result = []
    for text in texts:
        result.append({
            'description': text.description,
            'bounding_poly': text.bounding_poly.vertices
        })
    
    return result
"""


def run_quickstart() -> vision.EntityAnnotation:

    credentials = load_credentials_from_file("bbangguzipggu-430108-8fb65a8f56a8.json")
    print(credentials)

    print("credentials : ")
    print(credentials[0])

    print("project id : ")
    print(credentials[1])

    # Vision Client 생성
    client = vision.ImageAnnotatorClient(credentials=credentials[0])

    print("hello")

    file_uri = "gs://cloud-samples-data/vision/label/wakeupcat.jpg"

    image = vision.Image()

    print("bye")

    image.source.image_uri = file_uri

    print("byebyebye")

    # Performs label detection on the image file
    response = client.label_detection(image=image)

    print("yayayayayayaya")

    labels = response.label_annotations

    print("Labels:")
    for label in labels:
        print(label.description)

    return labels