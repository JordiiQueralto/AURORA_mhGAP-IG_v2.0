from elevenlabs.client import ElevenLabs
from elevenlabs import save

# Configuración del cliente
# Obtén tu API Key en elevenlabs.io
client = ElevenLabs(api_key="TU_API_KEY_ELEVENLABS")

def TTS(texto, nombre_archivo="respuesta_bot.mp3"):
    """
    Convierte texto en un archivo de audio .mp3
    """
    try:
        print("Generando audio...")
        audio = client.generate(
            text=texto,
            voice="Rachel", # Puedes cambiar el nombre de la voz aquí
            model="eleven_multilingual_v2"
        )
        
        # Guardamos el flujo de audio en un archivo local
        save(audio, nombre_archivo)
        return f"Audio guardado con éxito como {nombre_archivo}"
    
    except Exception as e:
        return f"Error en Texto a Voz: {e}"

def STT(ruta_audio):
    """
    Convierte un archivo de audio en texto (Speech to Text)
    """
    try:
        print("Transcribiendo audio...")
        with open(ruta_audio, "rb") as audio_file:
            # Usamos el modelo de transcripción de ElevenLabs
            transcripcion = client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v1", # El modelo de alta precisión de Eleven
            )
        return transcripcion.text
    except Exception as e:
        return f"Error en Voz a Texto: {e}"