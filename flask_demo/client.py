import requests

# Send a GET request
response = requests.get("http://127.0.0.1:5000/get_message")
print("GET response:", response.json())

# Send a POST request with JSON data
data = {"name": "Alice", "age": 30}
response = requests.post("http://127.0.0.1:5000/process_data", json=data)
print("POST response:", response.json())

try:
    response = requests.post("http://127.0.0.1:5000/run_script")
    # Check for successful response
    if response.status_code == 200:
        print("Server Response:", response.json()["message"])
        print("Script Output:", response.json()["output"])
    else:
        print("Server Response:", response.json()["message"])
        if "error" in response.json():
            print("Error Details:", response.json()["error"])
except requests.exceptions.RequestException as e:
    print("Request failed:", e)

#try
# response = requests.post("http://127.0.0.1:5000/shutdown")
#     if response.status_code == 200:
#         print("Server is shutting down...")
#     else:
#         print("Failed to shut down the server.")
# except requests.exceptions.RequestException as e:
#     print("Shutdown request failed:", e)
