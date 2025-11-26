"""
Generador de frases aleatorias para verificación de voz con challenge-response
Previene ataques de replay al requerir diferentes frases cada vez
"""

import random
import string
from datetime import datetime


class ChallengeGenerator:
    """Genera desafíos aleatorios para verificación de voz"""
    
    # Listas de palabras para generar frases
    SUSTANTIVOS = [
        "perro", "gato", "casa", "árbol", "mesa", "libro", "ventana", "puerta",
        "cielo", "sol", "luna", "estrella", "río", "montaña", "playa", "bosque",
        "ciudad", "coche", "avión", "barco", "tren", "música", "arte", "tiempo"
    ]
    
    ADJETIVOS = [
        "grande", "pequeño", "rápido", "lento", "brillante", "oscuro", "nuevo", "viejo",
        "feliz", "triste", "hermoso", "fuerte", "débil", "alto", "bajo", "caliente",
        "frío", "limpio", "sucio", "dulce", "amargo", "suave", "duro", "ligero"
    ]
    
    VERBOS = [
        "correr", "saltar", "nadar", "volar", "cantar", "bailar", "reír", "llorar",
        "hablar", "escuchar", "mirar", "pensar", "escribir", "leer", "comer", "beber",
        "dormir", "despertar", "jugar", "trabajar", "estudiar", "caminar", "subir", "bajar"
    ]
    
    COLORES = [
        "rojo", "azul", "verde", "amarillo", "negro", "blanco", "naranja", "morado",
        "rosa", "gris", "marrón", "dorado", "plateado", "celeste", "turquesa", "violeta"
    ]
    
    @staticmethod
    def generate_numeric_code(length=6):
        """
        Genera un código numérico aleatorio
        Ejemplo: "3-7-2-9-1-5"
        """
        digits = [str(random.randint(0, 9)) for _ in range(length)]
        return "-".join(digits)
    
    @staticmethod
    def generate_alphanumeric_code(length=6):
        """
        Genera un código alfanumérico aleatorio
        Ejemplo: "A-3-K-7-M-2"
        """
        chars = string.ascii_uppercase + string.digits
        code = [random.choice(chars) for _ in range(length)]
        return "-".join(code)
    
    @staticmethod
    def generate_word_sequence(count=4):
        """
        Genera una secuencia de palabras aleatorias
        Ejemplo: "azul casa rápido cantar"
        """
        all_words = (
            ChallengeGenerator.SUSTANTIVOS + 
            ChallengeGenerator.ADJETIVOS + 
            ChallengeGenerator.VERBOS +
            ChallengeGenerator.COLORES
        )
        words = random.sample(all_words, count)
        return " ".join(words)
    
    @staticmethod
    def generate_simple_phrase():
        """
        Genera una frase simple con estructura gramatical
        Ejemplo: "el gato pequeño corre rápido"
        """
        articulo = random.choice(["el", "la", "un", "una"])
        sustantivo = random.choice(ChallengeGenerator.SUSTANTIVOS)
        adjetivo = random.choice(ChallengeGenerator.ADJETIVOS)
        verbo = random.choice(ChallengeGenerator.VERBOS)
        
        estructuras = [
            f"{articulo} {sustantivo} {adjetivo}",
            f"{verbo} {articulo} {sustantivo}",
            f"{sustantivo} {adjetivo} {verbo}",
            f"{articulo} {sustantivo} {verbo}"
        ]
        
        return random.choice(estructuras)
    
    @staticmethod
    def generate_color_number():
        """
        Genera combinación de color y número
        Ejemplo: "azul siete"
        """
        numeros_texto = [
            "cero", "uno", "dos", "tres", "cuatro", "cinco",
            "seis", "siete", "ocho", "nueve", "diez"
        ]
        
        color = random.choice(ChallengeGenerator.COLORES)
        numero = random.choice(numeros_texto)
        
        return f"{color} {numero}"
    
    @staticmethod
    def generate_timestamp_based():
        """
        Genera frase basada en timestamp actual
        Ejemplo: "verificar 15 47 23" (hora actual)
        """
        now = datetime.now()
        return f"verificar {now.hour} {now.minute} {now.second}"
    
    @staticmethod
    def generate_mathematical():
        """
        Genera una operación matemática simple
        Ejemplo: "tres más cinco"
        """
        numeros_texto = [
            "cero", "uno", "dos", "tres", "cuatro", "cinco",
            "seis", "siete", "ocho", "nueve", "diez"
        ]
        
        num1 = random.randint(0, 10)
        num2 = random.randint(0, 10)
        operacion = random.choice(["más", "menos", "por"])
        
        return f"{numeros_texto[num1]} {operacion} {numeros_texto[num2]}"
    
    @staticmethod
    def generate_challenge(challenge_type="numeric"):
        """
        Genera un desafío según el tipo especificado
        
        Args:
            challenge_type: Tipo de desafío
                - "numeric": Código numérico (default)
                - "alphanumeric": Código alfanumérico
                - "words": Secuencia de palabras
                - "phrase": Frase simple
                - "color_number": Color + número
                - "timestamp": Basado en hora actual
                - "math": Operación matemática
                - "random": Elige uno al azar
        
        Returns:
            tuple: (challenge_text, display_format)
                challenge_text: Texto que el usuario debe decir
                display_format: Formato para mostrar en pantalla
        """
        
        if challenge_type == "random":
            challenge_type = random.choice([
                "numeric", "alphanumeric", "words", "phrase",
                "color_number", "math"
            ])
        
        generators = {
            "numeric": (
                ChallengeGenerator.generate_numeric_code,
                "Di los siguientes números:"
            ),
            "alphanumeric": (
                ChallengeGenerator.generate_alphanumeric_code,
                "Di el siguiente código:"
            ),
            "words": (
                ChallengeGenerator.generate_word_sequence,
                "Di las siguientes palabras:"
            ),
            "phrase": (
                ChallengeGenerator.generate_simple_phrase,
                "Di la siguiente frase:"
            ),
            "color_number": (
                ChallengeGenerator.generate_color_number,
                "Di el color y número:"
            ),
            "timestamp": (
                ChallengeGenerator.generate_timestamp_based,
                "Di la siguiente frase:"
            ),
            "math": (
                ChallengeGenerator.generate_mathematical,
                "Di la operación:"
            )
        }
        
        if challenge_type not in generators:
            challenge_type = "numeric"
        
        generator, display_format = generators[challenge_type]
        challenge_text = generator()
        
        return challenge_text, display_format
    
    @staticmethod
    def format_for_display(challenge_text, challenge_type="numeric"):
        """
        Formatea el texto del desafío para mostrar en pantalla
        """
        if challenge_type == "numeric":
            # Mostrar números grandes y separados
            return "  " + "   ".join(challenge_text.split("-"))
        elif challenge_type == "alphanumeric":
            # Mostrar caracteres grandes y separados
            return "  " + "   ".join(challenge_text.split("-"))
        else:
            # Mostrar texto normal
            return challenge_text
    
    @staticmethod
    def validate_response(challenge_text, user_response):
        """
        Valida que la respuesta del usuario contenga el desafío
        (Usado para verificación adicional opcional)
        
        Nota: La validación principal es por voz, esto es opcional
        """
        # Normalizar textos
        challenge_normalized = challenge_text.lower().replace("-", " ")
        response_normalized = user_response.lower()
        
        # Verificar si todas las palabras del desafío están en la respuesta
        challenge_words = challenge_normalized.split()
        
        matches = sum(1 for word in challenge_words if word in response_normalized)
        
        # Calcular porcentaje de coincidencia
        match_percentage = (matches / len(challenge_words)) * 100
        
        return match_percentage >= 70  # 70% de palabras deben coincidir


# Función de conveniencia
def generate_voice_challenge(challenge_type="numeric"):
    """
    Función de conveniencia para generar un desafío
    
    Args:
        challenge_type: Tipo de desafío (ver ChallengeGenerator.generate_challenge)
    
    Returns:
        tuple: (challenge_text, display_format)
    """
    return ChallengeGenerator.generate_challenge(challenge_type)


# Ejemplos de uso
if __name__ == "__main__":
    print("="*60)
    print("   EJEMPLOS DE DESAFÍOS ALEATORIOS")
    print("="*60)
    print()
    
    tipos = [
        "numeric", "alphanumeric", "words", "phrase",
        "color_number", "timestamp", "math"
    ]
    
    for tipo in tipos:
        challenge, display = ChallengeGenerator.generate_challenge(tipo)
        formatted = ChallengeGenerator.format_for_display(challenge, tipo)
        
        print(f"Tipo: {tipo}")
        print(f"Display: {display}")
        print(f"Challenge: {formatted}")
        print("-" * 60)
    
    print()
    print("="*60)
    print("   GENERANDO 5 DESAFÍOS ALEATORIOS")
    print("="*60)
    print()
    
    for i in range(5):
        challenge, display = ChallengeGenerator.generate_challenge("random")
        print(f"{i+1}. {display}")
        print(f"   '{challenge}'")
        print()