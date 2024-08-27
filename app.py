from flask import Flask, request, jsonify
import os
import shelve
from dotenv import load_dotenv
from openai import OpenAI
import json
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# =========================================

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Define assistant ID

ASSISTANT_ID = "asst_gG5MOjxPk6juhI7FoHCTFxy7"


# Thread management functions
def check_if_thread_exists(user_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(user_id, None)


def store_thread(user_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[user_id] = thread_id


def generate_response(message_body, user_id):
    # Check if there is already a thread_id for the user_id
    thread_id = check_if_thread_exists(user_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        print(f"Creating new thread for user_id {user_id}")
        thread = client.beta.threads.create()
        store_thread(user_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread for user_id {user_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # Retrieve the chat history
    chat_history = get_chat_history(thread_id)
    print(f"Chat history for user_id {user_id}: {chat_history}")

    # Add new message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(f"📤 Message Sent: {message.id}")

    # Run the assistant and get the new message
    new_message = run_assistant(thread)
    print(f"To user_id {user_id}: {new_message}")
    return new_message, chat_history


def get_chat_history(thread_id):
    # Retrieve all messages in the thread
    message_response = client.beta.threads.messages.list(thread_id=thread_id)
    messages = message_response.data

    # Extract and format the chat history
    chat_history = []
    for msg in messages:
        if hasattr(msg.content[0], "text"):
            chat_history.append(
                {"role": msg.role, "content": msg.content[0].text.value}
            )
        else:
            chat_history.append({"role": msg.role, "content": "No text content found."})

    return chat_history


# Function to run the assistant
def run_assistant(thread):
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    # Wait for completion
    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    message_response = client.beta.threads.messages.list(thread_id=thread.id)
    messages = message_response.data

    # Extract the assistant's reply from the messages
    assistant_reply = None
    for msg in messages:
        if msg.role == "assistant":
            assistant_reply = msg.content[0].text.value
            break

    if assistant_reply:
        print(f"Generated message: {assistant_reply}")
    else:
        assistant_reply = "No response from the assistant."
        print("No response from the assistant.")

    return assistant_reply


@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.json
    user_id = data.get("sysUserId")
    question = data.get("question")

    # Extract additional user data

    print(data)
    if data.get("weight"):
        print("===============================\n")
        print(data.get("weight"))
        print(data.get("height"))
        print(data.get("longitude"))
        print(data.get("latitude"))
        print(data.get("childName"))
        print(data.get("parentFirstName"))
        print(data.get("currentAge"))
        print("===============================\n")

        user_data = json.dumps(
            {
                "weight": data.get("weight"),
                "height": data.get("height"),
                "longitude": data.get("longitude"),
                "latitude": data.get("latitude"),
                "childName": data.get("childName"),
                "parentFirstName": data.get("parentFirstName"),
                "currentAge": data.get("age"),
                "sex": data.get("sex"),
                "question": question,
            }
        )
    else:
        user_data = json.dumps({"question": question})

    assistant_reply, chat_history = generate_response(user_data, user_id)
    print({"chat_history": chat_history})

    return jsonify({"reply": assistant_reply, "chat_history": chat_history})
    # return jsonify({"reply": assistant_reply})


if __name__ == "__main__":
    app.run(debug=True)
