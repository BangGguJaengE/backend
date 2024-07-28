from PIL import Image

def mock_object_detection() -> list[dict]:

    image1 = Image.open("src/mock/blue_sopa.png")
    image2 = Image.open("src/mock/white_bed.png")

    dic_list = [
        {
            "coordinate": (10, 30),
            "image": image1,
            "label": "bed"
        },
        {            
            "coordinate": (30, 50),
            "image": image2,
            "label": "couch"
        }
    ]

    return dic_list