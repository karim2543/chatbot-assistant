import os
import sys
import secrets
from flask import Flask
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
logging.getLogger("comtypes").setLevel(logging.WARNING)

from Blueprints.ChatBotBlueprint import chatbot_bp

def create_app():
    # Racine du projet
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Dossiers templates et static
    TEMPLATE_DIR = os.path.join(ROOT_DIR, "templates")
    STATIC_DIR = os.path.join(ROOT_DIR, "static")

    # Création de l'application Flask
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_urlsafe(32)

    # Enregistrer le blueprint
    app.register_blueprint(chatbot_bp, url_prefix="/chatbot")

    return app

# --- POINT D'ENTRÉE DU SERVEUR ---
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)