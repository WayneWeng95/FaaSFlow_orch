import requests

# Send a GET request
response = requests.get("http://127.0.0.1:5000/get_message")
print("GET response:", response.json())

# Send a POST request with JSON data
data = {"name": "Alice", "age": 30}
response = requests.post("http://127.0.0.1:5000/process_data", json=data)
print("POST response:", response.json())
