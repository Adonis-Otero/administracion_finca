# ia_provider.py
"""
Módulo de abstracción del proveedor de Inteligencia Artificial.

Actúa como una Fábrica (Factory Pattern) que lee el archivo .env
y devuelve el cliente de IA, el nombre del modelo y parámetros extra configurados.
Para cambiar de proveedor, solo se modifica IA_PROVIDER en el .env.

Proveedores soportados:
  - "lmstudio" : Servidor local de LM Studio (sin internet, privado)
  - "gemini"   : Google Gemini API (en la nube, requiere internet y API Key)
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Cargamos el archivo .env automáticamente al importar este módulo
load_dotenv()


def get_ia_client() -> tuple[OpenAI, str, dict]:
    """
    Lee la variable IA_PROVIDER del .env y devuelve una tupla
    (client, model_name, extra_kwargs) lista para usar en chat.completions.create().

    El campo extra_kwargs contiene parámetros adicionales específicos del proveedor
    que se pasan con **extra_kwargs en la llamada. Por ejemplo, Gemini 2.5 Flash
    requiere desactivar el razonamiento interno (thinking) para evitar que sus tokens
    internos consuman el presupuesto de max_tokens y trunquen la respuesta.

    Returns:
        (OpenAI, str, dict): Cliente configurado, nombre del modelo y kwargs extra.

    Raises:
        ValueError: Si el proveedor especificado no es reconocido.
    """
    proveedor = os.getenv("IA_PROVIDER", "lmstudio").strip().lower()

    if proveedor == "lmstudio":
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        model = os.getenv("LMSTUDIO_MODEL", "local-model")
        client = OpenAI(
            base_url=base_url,
            api_key="not-needed",  # LM Studio no requiere autenticación real
        )
        print(f"[IA Provider] Proveedor: LM Studio | Modelo: {model} | URL: {base_url}")
        return client, model, {"max_tokens": 1000}

    elif proveedor == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY no está definida en el archivo .env. "
                "Por favor, agrega tu clave de la API de Google AI Studio."
            )
        # Gemini expone un endpoint compatible con el protocolo OpenAI
        client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
        print(f"[IA Provider] Proveedor: Google Gemini | Modelo: {model}")
        # max_tokens alto para acomodar los tokens de razonamiento interno de Gemini 2.5 Flash
        # sin contar, que quede suficiente presupuesto para la respuesta JSON real.
        return client, model, {"max_tokens": 4096}

    else:
        raise ValueError(
            f"Proveedor de IA '{proveedor}' no reconocido. "
            "Opciones válidas en el .env: 'lmstudio' o 'gemini'."
        )
