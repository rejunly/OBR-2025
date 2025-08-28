# Este é um arquivo "mock" (falso) para simular o controle dos motores no PC.
# Ele apenas imprime no console as ações que seriam enviadas ao robô.

def setup_motors():
    """Simula a configuração inicial dos pinos e motores."""
    print("[SIMULADOR] Motores configurados para teste.")

def gerenciar_movimento(acao, erro=0):
    """
    Simula o gerenciamento do movimento com base na ação e no erro de linha.
    """
    print(f"[SIMULADOR] Comando Recebido: Ação = '{acao}', Erro = {erro}")
    # Aqui você poderia adicionar lógicas de impressão mais detalhadas se quisesse.
    # Ex: if acao == "Seguir em Frente": print("  -> Ajustando com base no erro...")

def stop_all_motors():
    """Simula a parada de todos os motores."""
    print("[SIMULADOR] ** PARADA DE EMERGÊNCIA / FIM ** Todos os motores parados.")

def full_stop_and_cleanup():
    """Simula a parada final e limpeza dos recursos (GPIOs no RPi)."""
    print("[SIMULADOR] Parada final e limpeza de recursos.")
