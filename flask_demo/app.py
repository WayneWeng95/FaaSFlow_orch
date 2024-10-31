from flask import Flask, jsonify, request
import subprocess
import signal
import os
import sys

app = Flask(__name__)

# Example data to return on request
sample_data = {
    "message": "Hello from the server!",
    "status": "success"
}

# Endpoint to get a simple message (GET request)

def run_firecracker():
        try:
            # Run the shell script
            command = ['./cold', firecracker_number, fibonacci_number]
            result = subprocess.run(
                command,
                text=True,  # Treat output as strings
                capture_output=True,  # Capture stdout and stderr
                check=True  # Raise CalledProcessError for non-zero exit codes
            )

            # Capture stdout and stderr from the script
            if result.returncode == 0:
                return jsonify({"message": "Script ran successfully!", "output": result.stdout}), 200
            else:
                return jsonify({"message": "Script execution failed!", "error": result.stderr}), 500
        except Exception as e:
            return jsonify({"message": "An error occurred while running the script.", "error": str(e)}), 500


def run_docker():
# Run the shell script
    command = ['docker', 'run', '-d', '--name', 'test-container', 'ubuntu', 'sleep', '1000']

    try:
        # Run the command
        result = subprocess.run(
            command,
            text=True,  # Treat output as strings
            capture_output=True,  # Capture stdout and stderr
            check=True  # Raise CalledProcessError for non-zero exit codes
        )

        # Print the output (container ID)
        print("Container started successfully. Container ID:")
        print(result.stdout.strip())  # Use strip() to remove any extra whitespace

    except subprocess.CalledProcessError as e:
        # Print the error output if the command fails
        print("An error occurred:")
        print(e.stderr.strip())  # Print error message

        # Capture stdout and stderr from the script
    #     if result.returncode == 0:
    #         return jsonify({"message": "Script ran successfully!", "output": result.stdout}), 200
    #     else:
    #         return jsonify({"message": "Script execution failed!", "error": result.stderr}), 500
    # except Exception as e:
    #     return jsonify({"message": "An error occurred while running the script.", "error": str(e)}), 500

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


@app.route("/run_script", methods=["POST"])
def run_script():
    try:
        # Run the shell script
        result = subprocess.run(
            ["./FaaSFlow_orch/flask_demo/script.sh"], capture_output=True, text=True)

        # Capture stdout and stderr from the script
        if result.returncode == 0:
            return jsonify({"message": "Script ran successfully!", "output": result.stdout}), 200
        else:
            return jsonify({"message": "Script execution failed!", "error": result.stderr}), 500
    except Exception as e:
        return jsonify({"message": "An error occurred while running the script.", "error": str(e)}), 500


@app.route("/run_function", methods=["POST"]) #determine which one to run by a flag
def run_function():
    run_firecracker()
    run_docker()



@app.route("/shutdown", methods=["POST"])
def shutdown():
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"message": "Server is shutting down..."}), 200

@app.route('/info', methods = ['GET'])
def info():
    return 0
#     return json.dumps(container_names)

if __name__ == "__main__":
    # Specify the port number here  app.run(debug=True, port=8000)
    app.run(debug=True)
