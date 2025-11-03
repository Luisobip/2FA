import numpy as np
import sounddevice as sd
from scipy.spatial.distance import cosine
from config import Config
import time

class VoiceAuth:
    """Autenticación por reconocimiento de voz"""
    
    def __init__(self):
        self.sample_rate = Config.VOICE_SAMPLE_RATE
        self.duration = Config.VOICE_DURATION
        self.phrase = Config.VOICE_PHRASE
        self.similarity_threshold = Config.VOICE_SIMILARITY_THRESHOLD
    
    def _extract_voice_features(self, audio_data):
        """Extrae características del audio para comparación"""
        audio_flat = audio_data.flatten()
        
        # Características temporales
        features = {
            'mean': np.mean(audio_flat),
            'std': np.std(audio_flat),
            'max': np.max(audio_flat),
            'min': np.min(audio_flat),
            'median': np.median(audio_flat),
            'energy': np.sum(audio_flat ** 2),
            'zero_crossing_rate': np.sum(np.abs(np.diff(np.sign(audio_flat)))) / len(audio_flat)
        }
        
        # Características espectrales (FFT)
        fft = np.fft.fft(audio_flat)
        magnitude = np.abs(fft[:len(fft)//2])
        features['spectral_centroid'] = np.sum(magnitude * np.arange(len(magnitude))) / np.sum(magnitude)
        features['spectral_rolloff'] = np.percentile(magnitude, 85)
        
        return features
    
    def _countdown(self, seconds=3):
        """Cuenta regresiva antes de grabar"""
        print(f"\nGrabando en {seconds} segundos...")
        for i in range(seconds, 0, -1):
            print(f"  {i}...", flush=True)
            time.sleep(1)
    
    def record_voice_sample(self, username):
        """Graba una muestra de voz del usuario para registro"""
        print(f"\n🎤 Grabación de muestra de voz")
        print(f"\nLee la siguiente frase en voz alta y CLARA:")
        print(f"┌─────────────────────────────────────────────────┐")
        print(f"│ '{self.phrase}' │")
        print(f"└─────────────────────────────────────────────────┘")
        
        input("\nPresiona ENTER cuando estés listo...")
        self._countdown()
        
        print(f"🔴 GRABANDO... ({self.duration} segundos)")
        try:
            audio_data = sd.rec(
                int(self.duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float64'
            )
            sd.wait()
            print("✅ Grabación completada")
            
            features = self._extract_voice_features(audio_data)
            return features
        except Exception as e:
            print(f"❌ Error durante la grabación: {e}")
            return None
    
    def verify_voice(self, username, stored_features):
        """Verifica la voz del usuario"""
        print(f"\n🎤 Verificación de voz")
        print(f"\nLee la siguiente frase en voz alta y CLARA:")
        print(f"┌─────────────────────────────────────────────────┐")
        print(f"│ '{self.phrase}' │")
        print(f"└─────────────────────────────────────────────────┘")
        
        input("\nPresiona ENTER cuando estés listo...")
        self._countdown()
        
        print(f"🔴 GRABANDO... ({self.duration} segundos)")
        try:
            audio_data = sd.rec(
                int(self.duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float64'
            )
            sd.wait()
            print("✅ Grabación completada")
            
            current_features = self._extract_voice_features(audio_data)
            
            # Comparar características usando similitud coseno
            stored_vector = np.array(list(stored_features.values()))
            current_vector = np.array(list(current_features.values()))
            
            # Normalizar vectores
            stored_norm = stored_vector / np.linalg.norm(stored_vector)
            current_norm = current_vector / np.linalg.norm(current_vector)
            
            similarity = 1 - cosine(stored_norm, current_norm)
            
            print(f"\n📊 Análisis:")
            print(f"  Similitud de voz: {similarity:.2%}")
            print(f"  Umbral requerido: {self.similarity_threshold:.2%}")
            
            is_valid = similarity > self.similarity_threshold
            
            if is_valid:
                print("  ✅ Voz verificada correctamente")
            else:
                print("  ❌ La voz no coincide")
            
            return is_valid
            
        except Exception as e:
            print(f"❌ Error durante la verificación: {e}")
            return False
        
        