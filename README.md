## ChatBot

ChatBot-Assistant is a Flask-based chatbot application that uses qwen2.5:3b Ollama model for text
responses and 'pyttsx3' to generate voice responses.

## Prerequisites

- Windows with Python 3.10 or newer;
- Ollama installed and available in the 'PATH';
- the Ollama model 'qwen2.5:3b'.

## Installation on Windows

From the project root directory:

in the terminal
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt


## Configuration

Copy '.env.example' to '.env', then define the variables in
the environment before starting the application. The project does not automatically load
'.env' files.

Variables:

- 'FLASK_SECRET_KEY': random Flask secret key;
- 'CHATBOT_USERNAME': initial user on a fresh database;
- 'CHATBOT_EMAIL': email address of the initial user;
- 'CHATBOT_PASSWORD': password of the initial user;
- 'OLLAMA_HISTORY_LIMIT': maximum number of historical messages sent to Ollama.

PowerShell example:

$env:FLASK_SECRET_KEY = "your-local-key"
$env:CHATBOT_USERNAME = "local-user"
$env:CHATBOT_EMAIL = "local-user@example.invalid"
$env:CHATBOT_PASSWORD = "your-local-password"


An existing local database that already contains a single user can be
reused without recreating that user. On a fresh database, all three
'CHATBOT_*' account variables are required.

## SQLite Initialization

The migration scripts use relative paths and must be
executed from the project root directory, in the following order:

py DB\migration\000_create_user_table.py
py DB\migration\001_create_conversations_table.py
py DB\migration\002_create_messages_table.py
py DB\migration\003_create_assistant_settings_table.py
py DB\migration\004_create_voice_messages_table.py
py DB\migration\005_create_intents_table.py


The 'DB/database.db' database and its associated files are local data and
must not be published.

## Ollama and Running the Application

In a terminal:

ollama run qwen2.5:3b

In another terminal, with the virtual environment activated:

py App\Flaskapp.py

The application is then available at
'[http://127.0.0.1:5000/chatbot/](http://127.0.0.1:5000/chatbot/)'.