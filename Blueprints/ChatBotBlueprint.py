from flask import Blueprint, render_template, request, jsonify, send_from_directory, session
import os
import logging

from Model.User import User
from Model.Conversation import Conversation
from Model.AssistantSettings import AssistantSettings
from Service.chatbot import chatbot, ConversationAccessError
from Service.voice import VoiceHandler
from Service.response import (
    ResponseGenerator,
    ResponseGenerationError,
)
from DB.connection import connect

# --- CONFIG ---
TEXT_FOLDER = os.path.join(os.path.dirname(__file__), "..", "text_responses")
os.makedirs(TEXT_FOLDER, exist_ok=True)

VOICE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "voice_responses")
os.makedirs(VOICE_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

chatbot_bp = Blueprint("chatbot", __name__, template_folder="templates")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "DB", "database.db")

# --- ENABLE WAL MODE (IMPORTANT) ---
def init_db():
    conn = connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.close()

init_db()

# --- UTILISATEUR CONFIGURE ---
configured_username = os.environ.get("chatbot_USERNAME")
configured_email = os.environ.get("chatbot_EMAIL")
configured_password = os.environ.get("chatbot_PASSWORD")

user = User.getByUserName(configured_username) if configured_username else None
if not user and not any((configured_username, configured_email, configured_password)):
    existing_users = User.all()
    if existing_users:
        user = existing_users[0]

if not user:
    if not all((configured_username, configured_email, configured_password)):
        raise RuntimeError(
            "Configure chatbot_USERNAME, chatbot_EMAIL and "
            "chatbot_PASSWORD before creating the first user."
        )
    user = User(
        username=configured_username,
        email=configured_email,
        password=configured_password,
    )
    user.save()

# --- ASSISTANT SETTINGS ---
settings_list = AssistantSettings.all()
if settings_list:
    settings = settings_list[0]
else:
    settings = AssistantSettings()
    settings.save()

# --- SERVICES ---
chat = chatbot(user=user)
res_gen = ResponseGenerator(settings=settings)
voice_handler = VoiceHandler(user=user)

# --------------------
# ROUTES
# --------------------

def _conversation_to_dict(conversation):
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }


def _message_to_dict(message):
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at,
        "voice_response": None,
    }


def _get_legacy_conversation():
    conversation_id = session.get("conversation_id")
    if conversation_id is not None:
        try:
            return chat.get_conversation(int(conversation_id))
        except (TypeError, ValueError, ConversationAccessError):
            session.pop("conversation_id", None)

    conversation = chat.create_conversation()
    session["conversation_id"] = conversation.id
    return conversation


def _generate_message_response(text, conversation_id):
    msg = chat.send_message(text, conversation_id=conversation_id)
    history = chat.get_history(conversation_id)
    text_resp = res_gen.generate_text_response(
        text,
        conversation_history=history,
        current_message_id=msg.id,
    )

    assistant_msg = chat.send_message(
        text_resp,
        conversation_id=conversation_id,
        role="assistant",
    )

    res_gen.enqueue_voice_response(
        text_resp,
        on_success=voice_handler.save_voice,
    )

    return {
        "user_message": _message_to_dict(msg),
        "assistant_message": {
            **_message_to_dict(assistant_msg),
        },
    }


def _ollama_error_response(error):
    logging.error("Ollama error: %s", error)
    return jsonify({"error": "The Ollama service is unavailable."}), 502

@chatbot_bp.route("/", methods=["GET"])
def index():
    return render_template("chatbot.html")


@chatbot_bp.route("/conversations", methods=["GET"])
def list_conversations():
    conversations = Conversation.normalize_titles(user.id)
    return jsonify([_conversation_to_dict(item) for item in conversations])


@chatbot_bp.route("/conversations", methods=["POST"])
def create_conversation():
    conversation = chat.create_conversation()
    return jsonify(_conversation_to_dict(conversation)), 201


@chatbot_bp.route("/conversations/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    try:
        chat.delete_conversation(conversation_id)
    except ConversationAccessError:
        return jsonify({"error": "Conversation not found or access denied."}), 404
    return jsonify({"deleted": conversation_id})


@chatbot_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    try:
        conversation = chat.get_conversation(conversation_id)
    except ConversationAccessError:
        return jsonify({"error": "Conversation not found or access denied."}), 404

    return jsonify({
        "conversation": _conversation_to_dict(conversation),
        "messages": [
            _message_to_dict(message)
            for message in chat.get_history(conversation.id)
        ],
    })


@chatbot_bp.route(
    "/conversations/<int:conversation_id>/messages",
    methods=["POST"],
)
def send_conversation_message(conversation_id):
    try:
        chat.get_conversation(conversation_id)
    except ConversationAccessError:
        return jsonify({"error": "Conversation not found or access denied."}), 404

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Message is empty"}), 400

    try:
        return jsonify(_generate_message_response(text, conversation_id))
    except ResponseGenerationError as error:
        return _ollama_error_response(error)


# Legacy route retained for the current interface. Its conversation is scoped
# to the Flask session and is never selected from another user's conversations.
@chatbot_bp.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")

    if not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Message is empty"}), 400

    logging.debug(f"Text received: {text}")
    requested_id = data.get("conversation_id")
    if requested_id is not None:
        try:
            conversation = chat.get_conversation(int(requested_id))
        except (TypeError, ValueError, ConversationAccessError):
            return jsonify({"error": "Conversation not found or access denied."}), 404
        session["conversation_id"] = conversation.id
    else:
        conversation = _get_legacy_conversation()

    try:
        return jsonify(_generate_message_response(text, conversation.id))
    except ResponseGenerationError as error:
        return _ollama_error_response(error)


# âœ… NEW_MESSAGES (OPTIMIZED)
@chatbot_bp.route("/new_messages", methods=["GET"])
def get_new_messages():
    last_id = request.args.get("last_id", type=int, default=0)
    conversation_id = request.args.get("conversation_id", type=int)
    if conversation_id is None:
        try:
            conversation_id = _get_legacy_conversation().id
        except ConversationAccessError:
            return jsonify({"error": "Conversation not found or access denied."}), 404
    else:
        try:
            chat.get_conversation(conversation_id)
        except ConversationAccessError:
            return jsonify({"error": "Conversation not found or access denied."}), 404

    conn = connect(DB_PATH, timeout=10)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content
        FROM messages
        WHERE id > ? AND conversation_id = ?
        ORDER BY id ASC
    """, (last_id, conversation_id))

    rows = cursor.fetchall()
    conn.close()

    new_msgs = [
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "voice_response": None,
            "conversation_id": conversation_id,
        }
        for row in rows
    ]

    return jsonify(new_msgs)


# (optional) history if needed
@chatbot_bp.route("/history", methods=["GET"])
def get_history():
    conversation_id = request.args.get("conversation_id", type=int)
    if conversation_id is None:
        try:
            conversation_id = _get_legacy_conversation().id
        except ConversationAccessError:
            return jsonify({"error": "Conversation not found or access denied."}), 404
    else:
        try:
            chat.get_conversation(conversation_id)
        except ConversationAccessError:
            return jsonify({"error": "Conversation not found or access denied."}), 404

    conn = connect(DB_PATH, timeout=10)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, role, content
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            "id": row[0],
            "role": row[1],
            "content": row[2],
            "voice_response": None,
            "conversation_id": conversation_id,
        }
        for row in rows
    ])


# --- FILES ---
@chatbot_bp.route("/text_responses/<filename>")
def get_text(filename):
    return send_from_directory(TEXT_FOLDER, filename)

@chatbot_bp.route("/voice_responses/<filename>")
def get_voice(filename):
    return send_from_directory(VOICE_FOLDER, filename)
