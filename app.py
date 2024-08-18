from flask import Flask, request, jsonify
import os
import shelve
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load environment variables
api_key = os.getenv('OPENAI_API_KEY')

# Ensure API key is set
if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# Initialize OpenAI client
openai.api_key = api_key


# Thread management functions
def check_if_thread_exists(user_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(user_id, [])


def store_thread(user_id, messages):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[user_id] = messages


def format_message_body(user_data, question):
    """
    Format the message body by combining user data with the question.
    """
    details = (
        f"Weight: {user_data.get('weight')}, "
        f"Height: {user_data.get('height')}, "
        f"Longitude: {user_data.get('longitude')}, "
        f"Latitude: {user_data.get('latitude')}, "
        f"Child Name: {user_data.get('childName')}, "
        f"Parent First Name: {user_data.get('parentFirstName')}, "
        f"Current Age: {user_data.get('currentAge')}, "
        f"Sex: {user_data.get('sex')}\n\n"
    )
    return details + "Question: " + question


def generate_response(message_body, user_id):
    # Retrieve or initialize message history
    messages = check_if_thread_exists(user_id)

    # Ensure messages is a list
    if not isinstance(messages, list):
        messages = []

    # Add user message to the history
    messages.append({"role": "user", "content": message_body})

    # Request OpenAI for a response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=messages, max_tokens=150
    )

    # Get the assistant's reply
    answer = response.choices[0].message["content"].strip()

    # Add assistant's message to the history
    messages.append({"role": "assistant", "content": answer})

    # Store the updated message history
    store_thread(user_id, messages)

    return answer


@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    user_id = data.get("sysUserId")
    question = data.get("question")

    # Extract additional user data
    user_data = {
        "weight": data.get("weight"),
        "height": data.get("height"),
        "longitude": data.get("longitude"),
        "latitude": data.get("latitude"),
        "childName": data.get("childName"),
        "parentFirstName": data.get("parentFirstName"),
        "currentAge": data.get("currentAge"),
        "sex": data.get("sex"),
    }

    # Ensure that userId and question are provided
    if not user_id or not question:
        return jsonify({"message": "userId and question are required"}), 400

    # Combine the user data with the question to create a formatted message
    message_body = format_message_body(user_data, question)

    try:
        # Generate a response and manage the thread
        answer = generate_response(message_body, user_id)
        return jsonify({"response": answer})

    except Exception as e:
        return jsonify({"message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
