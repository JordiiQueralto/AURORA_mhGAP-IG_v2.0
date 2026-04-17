import speech_recognition as sr
from gtts import gTTS
import os


def STT():
    """
    Escucha desde el micrófono y devuelve el texto reconocido.
    """
    
    # Inicializar reconocedor una sola vez
    recognizer = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("\n[Habla ahora...]")
            audio = recognizer.listen(source)

        texto = recognizer.recognize_google(audio, language="es-ES")
        return texto

    except sr.UnknownValueError:
        print("BOT : No entendí el audio")
        return None

    except sr.RequestError as e:
        print("Error con el servicio:", e)
        return None


def TTS(texto, archivo="respuesta.mp3"):
    """
    Convierte un texto en voz y reproduce el audio.
    """
    try:
        carpeta = "audio"
        ruta = os.path.join(carpeta, archivo)
        tts = gTTS(text=texto, lang="es")
        tts.save(ruta)
        os.system(f"start {ruta}")
    except Exception as e:
        print("Error en TTS:", e)


# Ejemplo de uso
##texto_usuario = STT()

##if texto_usuario:
##    print("Has dicho:", texto_usuario)
##    TTS(f"{texto_usuario}")