# gestion des messages vocaux
import os
from Model.VoiceMessage import VoiceMessage

class VoiceHandler:
    def __init__(self, user):
        self.user = user

    def get_voice_history(self):
        return VoiceMessage.get_by_user(self.user.id)
    
    def save_voice(self, file_path):
        print("SAVE VOICE:", file_path)
        vm = VoiceMessage(user_id=self.user.id, file_path=file_path)
        vm.save()
        return vm