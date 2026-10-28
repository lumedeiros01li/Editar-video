"""Plano de cortes da edicao leve (tempos no video original, em segundos).

Erros removidos: 0-6.6s (olhando pro lado + primeira tentativa da frase inicial),
31-32.2s (tentativa errada do "Ja aos 45") e o "Repara," repetido em 40.6s.
Pausas e respiracoes entre os trechos sao cortadas.
"""
SEGMENTS = [
    (6.57, 12.86),   # "Para se aposentar aos 60 anos com 10 mil de renda... de acordo com a sua idade?"
    (16.21, 20.30),  # "Comecando aos 25 anos, voce precisa de R$ 3.150"
    (23.41, 27.54),  # "aos 35 voce precisa de R$ 5.750 por mes"
    (32.20, 36.52),  # "Ja aos 45 voce precisa de mais de 12 mil reais por mes"
    (41.29, 48.10),  # "repara que comecar 10 anos depois quase dobra o valor..."
    (50.01, 53.93),  # "Agora me conta, em qual idade voce esta..."
]
FADE = 0.012  # fade curto em cada corte para nao estalar


def starts():
    out, acc = [], 0.0
    for a, b in SEGMENTS:
        out.append(acc)
        acc += b - a
    return out, acc
