"""
Sistema de autenticación de voz con CHALLENGE-RESPONSE
Genera frases aleatorias en cada verificación para prevenir ataques de replay
"""

import numpy as np
import sounddevice as sd
from scipy.signal import butter, filtfilt
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import librosa
from config import Config
from challenge_generator import ChallengeGenerator


class VoiceAuthChallenge:
    """
    Sistema de autenticación de voz con desafíos aleatorios
    Previene ataques de replay al requerir diferentes frases cada vez
    """
    
    def __init__(self):
        self.sample_rate = Config.VOICE_SAMPLE_RATE
        self.duration = Config.VOICE_DURATION
        self.similarity_threshold = getattr(Config, 'VOICE_SIMILARITY_THRESHOLD', 0.75)

        # Tipo de desafío por defecto
        self.challenge_type = getattr(Config, 'VOICE_CHALLENGE_TYPE', 'numeric')

        # Parámetros MFCC
        self.n_mfcc = 13
        self.n_fft = 2048
        self.hop_length = 512

        # Parámetros de detección de vivacidad
        self.enable_liveness = getattr(Config, 'VOICE_ENABLE_LIVENESS', True)
        self.energy_variance_threshold = getattr(Config, 'VOICE_MIN_ENERGY_VARIANCE', 0.005)
        self.zcr_variance_threshold = getattr(Config, 'VOICE_MIN_ZCR_VARIANCE', 0.0005)
        self.pitch_variance_threshold = getattr(Config, 'VOICE_MIN_PITCH_VARIANCE', 2)

    def generate_challenge(self):
        """
        Genera una frase de desafío aleatoria
        Retorna solo el texto del desafío (para compatibilidad con Flask)
        """
        challenge_text, display_format = ChallengeGenerator.generate_challenge(self.challenge_type)
        return challenge_text
    
    def _apply_bandpass_filter(self, audio, lowcut=300, highcut=3400):
        """Aplica filtro pasabanda para voz humana"""
        nyquist = self.sample_rate / 2
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, audio)
        return filtered
    
    def _normalize_audio(self, audio):
        """Normaliza el audio al rango [-1, 1]"""
        audio = audio.astype(np.float32)
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return audio
    
    def _remove_silence(self, audio, threshold=0.01):
        """Elimina silencios del inicio y final con umbral más permisivo"""
        window_size = int(self.sample_rate * 0.02)

        # Si el audio es muy corto, no procesar
        if len(audio) < window_size * 2:
            return audio

        energy = np.array([
            np.sum(audio[i:i+window_size]**2)
            for i in range(0, len(audio) - window_size, window_size)
        ])

        if np.max(energy) > 0:
            energy = energy / np.max(energy)

        voice_indices = np.where(energy > threshold)[0]

        # Si no hay suficientes índices, retornar audio completo
        if len(voice_indices) == 0:
            return audio

        # Añadir margen para no cortar demasiado
        start_idx = max(0, (voice_indices[0] - 1) * window_size)
        end_idx = min(len(audio), (voice_indices[-1] + 2) * window_size)

        trimmed_audio = audio[start_idx:end_idx]

        # Asegurar que el audio resultante no sea demasiado corto
        if len(trimmed_audio) < self.sample_rate * 0.5:  # Al menos 0.5 segundos
            return audio

        return trimmed_audio
    
    def _extract_mfcc_features(self, audio):
        """Extrae características MFCC + deltas y calcula estadísticas"""
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )

        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2)

        features = np.vstack([mfcc, mfcc_delta, mfcc_delta2])

        return features

    def _extract_speaker_embedding(self, mfcc_features):
        """
        Extrae un vector de embedding del hablante independiente del texto
        Calcula estadísticas sobre los MFCC que caracterizan la voz, no el contenido

        IMPORTANTE: Solo los primeros 13 coeficientes MFCC representan la voz del hablante.
        Los deltas (14-26) y delta-deltas (27-39) capturan información temporal/dinámica
        que varía mucho incluso para la misma persona diciendo cosas diferentes.
        """
        # Separar MFCC base (0-12) de deltas y delta-deltas
        mfcc_base = mfcc_features[:13, :]  # Solo los primeros 13 coeficientes

        # Calcular estadísticas SOLO sobre los MFCC base para mayor discriminación
        mean = np.mean(mfcc_base, axis=1)
        std = np.std(mfcc_base, axis=1)

        # Percentiles para capturar la distribución de las características del hablante
        percentile_10 = np.percentile(mfcc_base, 10, axis=1)
        percentile_25 = np.percentile(mfcc_base, 25, axis=1)
        percentile_50 = np.percentile(mfcc_base, 50, axis=1)
        percentile_75 = np.percentile(mfcc_base, 75, axis=1)
        percentile_90 = np.percentile(mfcc_base, 90, axis=1)

        # Rango intercuartílico - captura variabilidad
        iqr = percentile_75 - percentile_25

        # Rango completo
        mfcc_min = np.min(mfcc_base, axis=1)
        mfcc_max = np.max(mfcc_base, axis=1)
        mfcc_range = mfcc_max - mfcc_min

        # Skewness aproximado
        median = percentile_50
        skewness = mean - median

        # Concatenar todas las estadísticas
        embedding = np.concatenate([
            mean,           # 13 valores - características centrales de la voz
            std,            # 13 valores - variabilidad
            percentile_10,  # 13 valores
            percentile_25,  # 13 valores
            percentile_50,  # 13 valores (mediana)
            percentile_75,  # 13 valores
            percentile_90,  # 13 valores
            iqr,            # 13 valores - rango intercuartílico
            mfcc_range,     # 13 valores - rango total
            skewness        # 13 valores - asimetría
        ])

        # Vector de 130 dimensiones (13 * 10)
        return embedding
    
    def _extract_prosodic_features(self, audio):
        """Extrae características prosódicas"""
        rms = librosa.feature.rms(
            y=audio,
            frame_length=self.n_fft,
            hop_length=self.hop_length
        )[0]
        
        zcr = librosa.feature.zero_crossing_rate(
            audio,
            frame_length=self.n_fft,
            hop_length=self.hop_length
        )[0]
        
        try:
            pitches, magnitudes = librosa.piptrack(
                y=audio,
                sr=self.sample_rate,
                n_fft=self.n_fft,
                hop_length=self.hop_length
            )
            pitch = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch.append(pitches[index, t])
            pitch = np.array(pitch)
        except:
            pitch = np.zeros(len(rms))
        
        return {
            'rms': rms,
            'zcr': zcr,
            'pitch': pitch,
            'rms_variance': np.var(rms),
            'zcr_variance': np.var(zcr),
            'pitch_variance': np.var(pitch[pitch > 0]) if np.any(pitch > 0) else 0
        }
    
    def _check_liveness(self, prosodic_features):
        """Verifica vivacidad del audio"""
        checks = []
        messages = []
        
        energy_var = prosodic_features['rms_variance']
        energy_check = energy_var > self.energy_variance_threshold
        checks.append(energy_check)
        
        if energy_check:
            messages.append(f"✓ Energía natural ({energy_var:.6f})")
        else:
            messages.append(f"⚠️  Energía baja ({energy_var:.6f})")
        
        zcr_var = prosodic_features['zcr_variance']
        zcr_check = zcr_var > self.zcr_variance_threshold
        checks.append(zcr_check)
        
        if zcr_check:
            messages.append(f"✓ ZCR natural ({zcr_var:.6f})")
        else:
            messages.append(f"⚠️  ZCR bajo ({zcr_var:.6f})")
        
        pitch_var = prosodic_features['pitch_variance']
        pitch_check = pitch_var > self.pitch_variance_threshold
        checks.append(pitch_check)
        
        if pitch_check:
            messages.append(f"✓ Pitch natural ({pitch_var:.2f})")
        else:
            messages.append(f"⚠️  Pitch bajo ({pitch_var:.2f})")
        
        confidence = sum(checks) / len(checks)
        is_live = confidence >= 0.34
        
        if sum(checks) == 0:
            is_live = False
            messages.append("⚠️  Audio puede ser sintético")
        
        return is_live, confidence, messages
    
    def _compare_embeddings(self, embedding1, embedding2):
        """
        Compara embeddings de hablante usando distancia euclidiana normalizada
        con función de decaimiento ajustada para características de voz
        """
        try:
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)

            # Calcular distancia euclidiana
            euclidean_distance = np.linalg.norm(emb1 - emb2)

            # Normalizar la distancia dividiéndola por sqrt(dimensiones)
            # Esto da una "distancia promedio por dimensión"
            normalized_distance = euclidean_distance / np.sqrt(len(emb1))

            # Convertir distancia a similitud [0, 1]
            # Con distancia euclidiana, los valores son más altos que con coseno
            # decay_factor=22: misma persona ~55-65%, diferente persona ~25-35%
            decay_factor = 22.0
            similarity = np.exp(-normalized_distance / decay_factor)

            return similarity

        except Exception as e:
            print(f"\n   ⚠️  Error en comparación de embeddings: {e}")
            return 0.0

    def _compare_features_dtw(self, features1, features2):
        """Compara características usando DTW"""
        try:
            feat1 = np.array(features1)
            feat2 = np.array(features2)

            if feat1.ndim == 1:
                feat1 = feat1.reshape(-1, 1)
            if feat2.ndim == 1:
                feat2 = feat2.reshape(-1, 1)

            # Transponer para que cada fila sea un frame temporal
            feat1 = feat1.T
            feat2 = feat2.T

            # Calcular DTW
            distance, path = fastdtw(feat1, feat2, dist=euclidean)

            # Normalizar por el número de frames y dimensiones
            avg_length = (len(feat1) + len(feat2)) / 2
            n_features = feat1.shape[1]

            # Normalización mejorada para MFCC
            normalized_distance = distance / (avg_length * np.sqrt(n_features))

            # Convertir a similitud (0-1)
            similarity = 1 / (1 + normalized_distance)

            return similarity, normalized_distance

        except Exception as e:
            print(f"\n   ⚠️  Error en comparación DTW: {e}")
            return 0.0, float('inf')
    
    def _record_audio_with_challenge(self, challenge_text, display_format):
        """Graba audio mostrando el desafío al usuario"""
        print(f"\n{display_format}")
        print(f"\n   ╔{'═'*56}╗")
        print(f"   ║  {challenge_text:^52}  ║")
        print(f"   ╚{'═'*56}╝")
        
        print(f"\n⏱️  Duración: {self.duration} segundos")
        print("\n🔴 Grabando en 3...")
        
        import time
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        print("🎙️  ¡HABLA AHORA!\n")
        
        recording = sd.rec(
            int(self.duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        
        print("✅ Grabación completada\n")
        
        return recording.flatten()
    
    def _process_audio(self, audio):
        """Pipeline completo de procesamiento"""
        print("   🔄 Procesando audio...")

        audio = self._normalize_audio(audio)
        print("      ✓ Normalizado")

        audio = self._apply_bandpass_filter(audio)
        print("      ✓ Filtrado")

        audio = self._remove_silence(audio)
        print(f"      ✓ Silencios eliminados (duración: {len(audio)/self.sample_rate:.2f}s)")

        # Reducir umbral mínimo a 0.5 segundos (antes era 1.0)
        min_length = self.sample_rate * 0.5
        if len(audio) < min_length:
            print(f"      ⚠️  Audio muy corto: {len(audio)/self.sample_rate:.2f}s (mínimo: 0.5s)")
            return None, None, None

        mfcc_features = self._extract_mfcc_features(audio)
        print(f"      ✓ MFCC extraídos ({mfcc_features.shape})")

        # Extraer embedding del hablante (independiente del texto)
        speaker_embedding = self._extract_speaker_embedding(mfcc_features)
        print(f"      ✓ Embedding del hablante extraído ({speaker_embedding.shape[0]} dims)")

        prosodic_features = self._extract_prosodic_features(audio)
        print("      ✓ Características prosódicas extraídas")

        return mfcc_features, speaker_embedding, prosodic_features
    
    def record_voice_sample(self, username):
        """
        Graba múltiples muestras con DIFERENTES FRASES para crear perfil de voz
        Text-independent speaker verification
        """
        print(f"\n{'='*60}")
        print("   REGISTRO DE VOZ CON DESAFÍOS ALEATORIOS")
        print(f"{'='*60}")
        
        print(f"\n📋 Nuevo Sistema de Seguridad:")
        print(f"   • Se grabarán 5 muestras con FRASES DIFERENTES")
        print(f"   • Esto crea un perfil de tu voz único")
        print(f"   • En cada inicio de sesión dirás una frase ALEATORIA")
        print(f"   • Previene ataques de replay (grabaciones)")
        
        print(f"\n💡 Consejos:")
        print(f"   • Ambiente silencioso")
        print(f"   • Habla con naturalidad")
        print(f"   • Di cada frase claramente")
        
        input("\nPresiona ENTER para comenzar...")
        
        # Grabar 5 muestras con diferentes frases
        samples = []
        num_samples = 5
        
        for i in range(num_samples):
            print(f"\n{'─'*60}")
            print(f"   MUESTRA {i+1} de {num_samples}")
            print(f"{'─'*60}")
            
            # Generar desafío aleatorio
            challenge, display = ChallengeGenerator.generate_challenge(self.challenge_type)
            
            # Grabar
            audio = self._record_audio_with_challenge(challenge, display)

            # Procesar
            mfcc_features, speaker_embedding, prosodic_features = self._process_audio(audio)

            if mfcc_features is None:
                print("   ❌ Muestra inválida")
                # Reintentar esta muestra
                i -= 1
                continue

            # Calcular calidad
            quality = (
                prosodic_features['rms_variance'] * 100 +
                prosodic_features['zcr_variance'] * 1000 +
                prosodic_features['pitch_variance']
            )

            print(f"\n   📊 Calidad: {quality:.2f}")

            # Guardar muestra
            samples.append({
                'mfcc': mfcc_features,
                'embedding': speaker_embedding,
                'prosodic': prosodic_features,
                'quality': quality,
                'challenge': challenge
            })
            
            print(f"   ✓ Muestra {i+1} guardada")
            
            if i < num_samples - 1:
                import time
                print("\n   Preparando siguiente frase...")
                time.sleep(2)
        
        if len(samples) == 0:
            print("\n❌ No se pudo obtener muestras válidas")
            return None
        
        print(f"\n{'='*60}")
        print("✅ PERFIL DE VOZ CREADO")
        print(f"   Muestras registradas: {len(samples)}")
        print(f"   Calidad promedio: {np.mean([s['quality'] for s in samples]):.2f}")
        print(f"{'='*60}")
        
        # Guardar todas las muestras
        voice_data = {
            'samples': samples,
            'num_samples': len(samples),
            'challenge_type': self.challenge_type,
            'version': 'challenge-response-v2'  # Nueva versión con embeddings
        }

        return voice_data
    
    def verify_voice(self, username, stored_features):
        """
        Verifica identidad con FRASE ALEATORIA
        Text-independent verification usando embeddings del hablante
        """
        print(f"\n{'='*60}")
        print("   VERIFICACIÓN DE VOZ CON DESAFÍO ALEATORIO")
        print(f"{'='*60}")

        # Verificar formato de datos
        if not isinstance(stored_features, dict) or 'version' not in stored_features:
            print("\n⚠️  Datos en formato antiguo detectados")
            print("💡 Re-registra tu voz para usar el nuevo sistema con desafíos")
            print("\n   Por ahora, no se puede verificar con desafío aleatorio")
            return False

        version = stored_features.get('version')
        if version not in ['challenge-response-v1', 'challenge-response-v2']:
            print("\n⚠️  Versión de datos incompatible")
            return False

        # Generar desafío aleatorio
        challenge, display = ChallengeGenerator.generate_challenge(self.challenge_type)

        print(f"\n🎲 Desafío Aleatorio Generado")
        print(f"   Este desafío es ÚNICO para esta sesión")
        print(f"   Previene ataques de replay\n")

        input("Presiona ENTER para comenzar la verificación...")

        # Grabar respuesta del usuario
        audio = self._record_audio_with_challenge(challenge, display)

        # Procesar
        mfcc_features, speaker_embedding, prosodic_features = self._process_audio(audio)

        if mfcc_features is None:
            print("❌ Audio inválido")
            return False

        # Verificar vivacidad (si está habilitado)
        if self.enable_liveness:
            print(f"\n{'─'*60}")
            print("   🔍 VERIFICANDO VIVACIDAD")
            print(f"{'─'*60}")

            is_live, confidence, messages = self._check_liveness(prosodic_features)

            for msg in messages:
                print(f"   {msg}")

            print(f"\n   Confianza: {confidence*100:.1f}%")

            if not is_live:
                print(f"\n   ⚠️  Advertencia: Detección de vivacidad falló")
                print(f"   Continuando verificación...")

        # Comparar con muestras almacenadas
        print(f"\n{'─'*60}")
        print("   🔍 COMPARANDO CON PERFIL DE VOZ")
        print(f"{'─'*60}")

        stored_samples = stored_features['samples']
        similarities = []

        print(f"\n   Comparando con {len(stored_samples)} muestras...")

        # Usar embeddings si están disponibles (v2), sino usar MFCC (v1)
        use_embeddings = version == 'challenge-response-v2'

        for idx, sample in enumerate(stored_samples):
            if use_embeddings and 'embedding' in sample:
                # Comparar embeddings usando distancia coseno
                stored_embedding = sample['embedding']
                similarity = self._compare_embeddings(speaker_embedding, stored_embedding)
            else:
                # Fallback a comparación DTW de MFCC
                stored_mfcc = sample['mfcc']
                similarity, _ = self._compare_features_dtw(mfcc_features, stored_mfcc)

            similarities.append(similarity)
            print(f"   Muestra {idx+1}: {similarity*100:.2f}%")
        
        # Usar similitud promedio
        avg_similarity = np.mean(similarities)
        max_similarity = np.max(similarities)
        
        print(f"\n   📊 Similitud promedio: {avg_similarity*100:.2f}%")
        print(f"   📊 Similitud máxima: {max_similarity*100:.2f}%")
        print(f"   🎯 Umbral requerido: {self.similarity_threshold*100:.2f}%")
        
        # Decisión: usar promedio de las 3 mejores muestras
        top_3_similarities = sorted(similarities, reverse=True)[:3]
        final_similarity = np.mean(top_3_similarities)
        
        print(f"\n   🎯 Similitud final (top-3): {final_similarity*100:.2f}%")
        
        is_match = final_similarity >= self.similarity_threshold
        
        if is_match:
            print(f"\n{'='*60}")
            print("✅ VERIFICACIÓN EXITOSA")
            print(f"   Identidad confirmada con {final_similarity*100:.2f}%")
            print(f"   Frase del desafío: '{challenge}'")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("❌ VERIFICACIÓN FALLIDA")
            print(f"   Similitud insuficiente ({final_similarity*100:.2f}%)")
            print(f"{'='*60}")
        
        return is_match