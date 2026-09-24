"""Testes do mazo_core.lembretes: janelas e estado de envio."""

from datetime import datetime, timedelta

from mazo_core import lembretes


def test_janela_horas_padrao_24h():
    agora = datetime(2026, 9, 24, 10, 0)
    ini, fim = lembretes.janela_horas(24, agora)
    assert ini == agora + timedelta(hours=23)
    assert fim == agora + timedelta(hours=25)


def test_janela_minutos_1h_margem_15min():
    agora = datetime(2026, 9, 24, 10, 0)
    ini, fim = lembretes.janela_minutos(60, agora, margem_min=15)
    assert ini == agora + timedelta(minutes=45)
    assert fim == agora + timedelta(minutes=75)


def test_derivar_status_enviada():
    assert lembretes.derivar_status("mid-1", configurado=True) == "ENVIADA"
    assert lembretes.derivar_status("mid-1", configurado=False) == "ENVIADA"


def test_derivar_status_falha_quando_configurado():
    assert lembretes.derivar_status(None, configurado=True) == "FALHA"


def test_derivar_status_simulada_quando_nao_configurado():
    assert lembretes.derivar_status(None, configurado=False) == "SIMULADA"


def test_marca_notificado():
    assert lembretes.marca_notificado("mid-1", True) is True
    assert lembretes.marca_notificado(None, False) is True   # simulado conta
    assert lembretes.marca_notificado(None, True) is False    # falha de real nao conta
