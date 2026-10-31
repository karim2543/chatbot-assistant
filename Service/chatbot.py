from Model.User import User
from Model.Conversation import Conversation
from Model.Message import Message
from Model.VoiceMessage import VoiceMessage


class ConversationAccessError(Exception):
    """Raised when a conversation does not exist or is not owned by the user."""

class chatbot:
    def __init__(self, user: User):
        self.user = user

    def get_conversation(self, conversation_id):
        conversation = Conversation.get(conversation_id)
        if conversation is None or conversation.user_id != self.user.id:
            raise ConversationAccessError("Conversation not found or access denied.")
        return conversation

    def create_conversation(self, title="New conversation"):
        conversations = Conversation.normalize_titles(self.user.id)
        conversation = Conversation(
            user_id=self.user.id,
            title=f"Conversation {len(conversations) + 1}",
        )
        conversation.save()
        return conversation

    def ensure_conversation(self, conversation_id=None, title="New conversation"):
        if conversation_id is None:
            raise ConversationAccessError("conversation_id is required.")
        return self.get_conversation(conversation_id)

    # --- Envoyer un message texte ---
    def send_message(self, text, conversation_id=None, role="user"):
        conv = self.ensure_conversation(conversation_id)
        msg = Message(conversation_id=conv.id, role=role, content=text)
        msg.save()
        return msg

    # --- Envoyer un message vocal ---
    def send_voice(self, file_path, conversation_id, transcript=None):
        conv = self.ensure_conversation(conversation_id)

        # 1️⃣ sauvegarder le fichier vocal
        voice_msg = VoiceMessage(user_id=self.user.id, file_path=file_path)
        voice_msg.save()

        # 2️⃣ sauvegarder le message texte correspondant (transcript)
        if transcript is None:
            transcript = "[Transcription unavailable]"
        msg = Message(conversation_id=conv.id, role="user", content=transcript)
        msg.save()

        return voice_msg, msg

    # --- Récupérer l'historique ---
    def get_history(self, conversation_id):
        conv = self.ensure_conversation(conversation_id)
        return Message.get_by_conversation(conv.id)

    def delete_conversation(self, conversation_id):
        conversation = self.get_conversation(conversation_id)
        conversation.delete()
        Conversation.normalize_titles(self.user.id)