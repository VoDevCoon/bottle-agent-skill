import requests

# 1. The URL of your LOCAL server (running in the other terminal)
url = "http://127.0.0.1:8000/process-bottle/"

# 2. Pick the image you want to test
# Make sure this file exists in your folder!
image_filename = "test111.png"  # <--- REPLACE THIS with your actual file name

print(f"Sending {image_filename} to local API...")

try:
    with open(image_filename, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        print("✅ Success! Image processed.")
        # Save the result to check it
        with open("test_result.png", "wb") as f:
            f.write(response.content)
        print("Saved result to: test_result.png")
    else:
        print(f"❌ Error {response.status_code}:")
        print(response.text)

except Exception as e:
    print(f"❌ Connection Failed: {e}")