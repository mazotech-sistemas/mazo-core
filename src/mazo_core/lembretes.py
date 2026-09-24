"""Motor de lembretes (janelas + estado de envio).

A busca de agendamentos fica no consumidor (modelos ORM diferentes por
vertical). Esta camada so decide:
- qual a janela temporal de "comeca em X horas" (com margem de erro)
- qual o estado do envio (ENVIADA / FALHA / SIMULADA)
- se o telefone entra na lista de notificados
"""
from datetime import datetime, timedelta


def janela_horas(horas: int, agora: datetime, margem_h: float = 1.0) -> tuple[datetime, datetime]:
    """Janela [inicio, fim] para lembrete de N horas antes do comeco.

    Padrao do sistema: margem de 1h (lembrete_24h) ou 15min (lembrete_1h).
    """
    ini = agora + timedelta(hours=horas - margem_h)
    fim = agora + timedelta(hours=horas + margem_h)
    return ini, fim


def janela_minutos(minutos: int, agora: datetime, margem_min: float = 15.0) -> tuple[datetime, datetime]:
    ini = agora + timedelta(minutes=minutos - margem_min)
    fim = agora + timedelta(minutes=minutos + margem_min)
    return ini, fim


def derivar_status(wa_id: str | None, configurado: bool) -> str:
    """Estado do envio conforme o id retornado e a configuracao do canal.

    - com wa_id: ENVIADA
    - sem wa_id + canal configurado: FALHA
    - sem wa_id + canal nao configurado (simulado): SIMULADA
    """
    if wa_id:
        return "ENVIADA"
    return "FALHA" if configurado else "SIMULADA"


def marca_notificado(wa_id: str | None, configurado: bool) -> bool:
    """Telefone entra na lista de notificados se enviou ou esta em modo simulado."""
    return bool(wa_id) or not configurado
