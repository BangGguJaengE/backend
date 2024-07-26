import requests
import json

url = "https://modelslab.com/api/v5/interior"

payload = json.dumps({
  "key": "",
  "init_image" : "https://raw.githubusercontent.com/BangGguJaengE/backend/main/app/stabledesign/data/general_room/test_room_resize.jpg",
  "prompt" : "A simple and clean room, 8k, photorealistic",
  "num_inference_steps" : 21,
  "base64" : "no",
  "guidance_scale" : 7
})

headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)