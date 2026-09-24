"""mazo-core: camada compartilhada Mazotech.

Submodulos:
- mazo_core.auth: JWT (HS256 fixo, fail-fast) + bcrypt
  (o import exige JWT_SECRET valido; so importar quem precisa)
- mazo_core.whatsapp: abstracao de canais (oficial/embutido/simulado)
- mazo_core.lembretes: motor de janelas e estado de envio
"""
__version__ = "0.1.0"
__all__ = ["auth", "whatsapp", "lembretes", "__version__"]
