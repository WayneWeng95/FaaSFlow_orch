from flask import Flask, jsonify, request

app = Flask(__name__)

# Example data to return on request
sample_data = {
    "message": "Hello from the server!",
    "status": "success"
}

# Endpoint to get a simple message (GET request)
@app.route("/get_message", methods=["GET"])
def get_message():
    return jsonify(sample_data), 200

# Endpoint to process data sent by the client (POST request)
@app.route("/process_data", methods=["POST"])
def process_data():
    if request.is_json:
        data = request.get_json()  # Parse JSON data from the request
        response_message = {
            "received_data": data,
            "message": "Data processed successfully!",
            "status": "success"
        }
        return jsonify(response_message), 200
    else:
        return jsonify({"message": "Request data must be in JSON format", "status": "error"}), 400

if __name__ == "__main__":
    app.run(debug=True)         # Specify the port number here  app.run(debug=True, port=8000)
