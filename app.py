from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import speech_recognition as sr
import pyttsx3
import threading
import json
import datetime
import requests
import os
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
CORS(app)

# Initialize text-to-speech engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)  # Speed of speech
tts_engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)

# Initialize speech recognition
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Global variable to store conversation history
conversation_history = []

class VoiceAssistant:
    def __init__(self):
        self.is_listening = False
        self.commands = {
            'waktu': self.get_time,
            'tanggal': self.get_date,
            'cuaca': self.get_weather,
            'kelompok': self.get_group,  # Tambahkan perintah kelompok
            'help': self.show_help,
            'bantuan': self.show_help
        }
    
    def speak(self, text):
        """Convert text to speech"""
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"Error in speech: {e}")
            return False
    
    def listen(self):
        """Listen to microphone and convert speech to text"""
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            with microphone as source:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            try:
                text = recognizer.recognize_google(audio, language='id-ID')
                print(f"Recognized: {text}")
                return text.lower()
            except sr.UnknownValueError:
                return "Maaf, saya tidak bisa mendengar dengan jelas"
            except sr.RequestError:
                return "Error: Tidak bisa terhubung ke layanan speech recognition"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def process_command(self, text):
        """Process voice command and return response"""
        if not text or text.startswith("error") or text.startswith("maaf"):
            return text
        
        # Add to conversation history
        conversation_history.append({
            'type': 'user',
            'text': text,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })
        
        response = "Maaf, saya tidak mengerti perintah tersebut."
        
        # Check for specific commands
        for command, func in self.commands.items():
            if command in text:
                response = func(text)
                break
        else:
            # Default responses for common greetings
            if any(word in text for word in ['halo', 'hai', 'hello', 'selamat']):
                response = "Halo! Saya adalah asisten suara Anda. Bagaimana saya bisa membantu?"
            elif any(word in text for word in ['terima kasih', 'thanks', 'makasih']):
                response = "Sama-sama! Senang bisa membantu Anda."
            elif any(word in text for word in ['siapa', 'apa', 'kamu']):
                response = "Saya adalah asisten suara yang dibuat untuk membantu Anda dengan berbagai tugas."
        
        # Add response to conversation history
        conversation_history.append({
            'type': 'assistant',
            'text': response,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })
        
        return response
    
    def get_time(self, text):
        """Get current time"""
        now = datetime.datetime.now()
        time_str = now.strftime('%H:%M')
        return f"Sekarang pukul {time_str}"
    
    def get_date(self, text):
        """Get current date"""
        now = datetime.datetime.now()
        days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
        
        day_name = days[now.weekday()]
        month_name = months[now.month - 1]
        
        return f"Hari ini {day_name}, {now.day} {month_name} {now.year}"
    
    def get_weather(self, text):
        """Get weather information (mock data)"""
        return "Cuaca hari ini cerah dengan suhu sekitar 28 derajat celsius"
    
    def search_web(self, text):
        """Search web"""
        query = text.replace('cari', '').strip()
        return f"Mencari informasi tentang: {query}"
    
    def get_group(self, text):
        """Return group members"""
        return "Anggota kelompok: AKMAL ZEN, MOHAMMAD RIFALDHI, RAYHAN NURAHMAN, DAMAR DWIYANTO, DRAJAT WIBOWO"
    
    def show_help(self, text):
        """Show available commands"""
        help_text = """
        Perintah yang tersedia:
        - Tanya waktu: "berapa waktu sekarang?"
        - Tanya tanggal: "tanggal berapa hari ini?"
        - Tanya cuaca: "bagaimana cuaca hari ini?"
        - Kelompok: "siapa anggota kelompok?"
        """
        return help_text.strip()

# Initialize assistant
assistant = VoiceAssistant()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/listen', methods=['POST'])
def listen():
    """API endpoint to listen to voice input"""
    try:
        text = assistant.listen()
        return jsonify({
            'success': True,
            'text': text,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/process', methods=['POST'])
def process():
    """API endpoint to process text command"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        response = assistant.process_command(text)
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/speak', methods=['POST'])
def speak():
    """API endpoint to convert text to speech"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        # Run speech in separate thread to avoid blocking
        thread = threading.Thread(target=assistant.speak, args=(text,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Speech started'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/conversation', methods=['GET'])
def get_conversation():
    """Get conversation history"""
    return jsonify({
        'success': True,
        'conversation': conversation_history[-10:]  # Last 10 messages
    })

@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return jsonify({
        'success': True,
        'message': 'Conversation cleared'
    })

if __name__ == '__main__':
    print("Starting Voice Assistant Server...")
    print("Make sure to install required packages:")
    print("pip install flask flask-cors speechrecognition pyttsx3 pyaudio")
    app.run(debug=True, port=5000)
