#npl_handler.py
import spacy

nlp = spacy.load("en_core_web_sm")

def register_nlp_handlers(app):
    @app.message("")
    def handle_message(message, say):
        doc = nlp(message['text'])
        
        subject = next((token.text for token in doc if token.dep_ == "nsubj"), None)
        
        if subject:
            say(f"You mentioned {subject}. I'll look that up for you.")
        else:
            say("I'm not sure I understood that. Could you rephrase?")