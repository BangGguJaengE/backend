import pytest
from fastapi.testclient import TestClient
from main import app  # FastAPI 애플리케이션이 정의된 모듈을 import

client = TestClient(app)

def test_transform_room_with_real_image():
    # 실제 이미지 파일 경로 설정
    image_path = "/Users/timdalxx/2024/zerodeling/backend-copy/app/stabledesign/data/general_room/test_room.jpg"

    # 이미지 파일 열기
    with open(image_path, "rb") as image_file:
        # FastAPI 엔드포인트에 이미지와 스타일 프롬프트 전송
        response = client.post(
            "/transform-room",
            files={"file": (image_path, image_file, "image/jpeg")},
            data={"style_prompt": "A modern room, photorealistic, 4k"}
        )

    data = response.json()
    print(data)  # 디버깅을 위해 응답 데이터 출력
    assert response.status_code == 200


    # 정상 응답 구조 확인
    assert "status" in data and data["status"] == "success"
    assert "output" in data and isinstance(data["output"], list)
    assert len(data["output"]) > 0 and isinstance(data["output"][0], str)

    # 비정상 응답 구조 확인 (테스트에서 실제로 발생하진 않음, 참조용)
    if data["status"] == "failed":
        assert "error_log" in data
        assert "response" in data["error_log"]
        assert "message" in data["error_log"]["response"]

# pytest가 기본적으로 이 파일의 모든 테스트 함수를 실행합니다.
