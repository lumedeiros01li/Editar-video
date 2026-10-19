#!/usr/bin/env python3
"""
Resolve o plano de edição (ancoras em palavras -> segundos) e verifica as regras.

Uso:
    python preparar_plano.py plano.json
Gera plano_resolvido.json ao lado do plano e imprime o relatório de verificação.
Resolve o estilo (blueprint ou brutalista). Sem "estilo" no plano, escolhe pelo conteúdo.
Sai com código 1 se houver ERRO (o render não deve rodar assim).
"""
import json
import os
import re
import subprocess
import sys

ANTECIPA = 0.06          # visual entra 2 quadros antes da palavra: soa sincronizado
CARTOES = {"numero", "lista", "comparacao", "grafico", "palavra", "conta", "carimbo"}
TIPOS = CARTOES | {"titulo", "zoom", "emoji", "aviso", "cta", "sticker"}
DUR_PADRAO = {"emoji": 1.2, "palavra": 1.4, "zoom": 1.6, "numero": 3.0, "aviso": 3.0,
              "titulo": 2.6, "grafico": 3.6, "cta": 3.0, "carimbo": 1.6, "sticker": 1.8}
ESTILOS = {"blueprint", "brutalista"}
SO_DE = {"carimbo": "brutalista", "sticker": "brutalista"}
ZOOM_PADRAO = {"blueprint": "suave", "brutalista": "seco"}
SETA_DUPLA = re.compile(r"»|«|≫|≪|>>|<<|›\s*›|‹\s*‹")
PISTAS = {
    "blueprint": r"\b(quanto|conta|calcul\w*|simula\w*|por m[eê]s|juros|rend\w*|precis\w*|multiplic\w*|soma|dividi\w*)\b",
    "brutalista": r"\b(mito|fato|verdade|mentira|erro|errad\w*|cuidado|alerta|lei|regra|proibid\w*|nunca|golpe)\b",
}
PROIBIDOS = [
    r"blindagem", r"garantid[oa]s?", r"sem risco", r"risco zero", r"renda certa",
    r"dobr\w* (o |seu |teu )?dinheiro", r"lucro f[aá]cil", r"retorno certo",
    r"enriquec\w* r[aá]pido", r"(rentabilidade|retorno) garantid",
]
LIMITES = {"titulo": 9, "palavra": 2, "cta": 8}
LIMITE_TITULO = {"blueprint": 9, "brutalista": 8}


def limpar(s):
    return re.sub(r"\*\*|\[\[|\]\]", "", str(s or ""))


def n_palavras(s):
    # "R$ 10" conta como uma palavra: o símbolo colado ao número é lido junto
    return len(re.sub(r"R\$\s+(?=\d)", "R$", limpar(s)).split())


def duracao_video(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        return float(p.stdout.decode().strip())
    except ValueError:
        sys.exit(f"ERRO: não consegui ler a duração de {path}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    caminho = os.path.abspath(sys.argv[1])
    base = os.path.dirname(caminho)
    plano = json.load(open(caminho, encoding="utf-8"))
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)  # noqa: E731

    erros, avisos, notas = [], [], []

    video = rel(plano["video"])
    if not os.path.isfile(video):
        sys.exit(f"ERRO: vídeo não encontrado: {video}")
    dur = duracao_video(video)
    fps = float(plano.get("fps", 30))

    trans = json.load(open(rel(plano["transcricao"]), encoding="utf-8"))
    palavras = trans["palavras"] if isinstance(trans, dict) else trans
    if not palavras:
        erros.append("Transcrição vazia: a legenda não tem palavras.")

    # ---------------------------------------------------- estilo
    estilo = plano.get("estilo")
    if estilo is None:
        fala_txt = " ".join(w["texto"] for w in palavras).lower()
        pts = {"blueprint": 0.0, "brutalista": 0.0}
        motivos = {"blueprint": [], "brutalista": []}
        for ev in plano.get("eventos", []):
            tp = ev.get("tipo")
            if tp in {"conta", "grafico", "comparacao", "numero"}:
                pts["blueprint"] += 3 if tp == "conta" else 1
                motivos["blueprint"].append(tp)
            if tp in {"lista", "carimbo", "sticker"}:
                pts["brutalista"] += 3 if tp == "carimbo" else 1
                motivos["brutalista"].append(tp)
        for est, pat in PISTAS.items():
            achados = re.findall(pat, fala_txt)
            pts[est] += 0.5 * len(achados)
            motivos[est] += [f"fala: {a}" for a in achados[:3]]
        estilo = "blueprint" if pts["blueprint"] >= pts["brutalista"] else "brutalista"
        notas.append(f"Estilo escolhido pelo conteúdo: {estilo} ({pts['blueprint']:.1f} x {pts['brutalista']:.1f}; "
                     f"{', '.join(dict.fromkeys(motivos[estilo])) or 'empate'}). Para forçar o outro, "
                     "ponha \"estilo\" no plano.")
    if estilo not in ESTILOS:
        erros.append(f"estilo '{estilo}' não existe. Use blueprint ou brutalista.")
        estilo = "blueprint"

    def t_palavra(i, campo="ini"):
        if not (0 <= i < len(palavras)):
            raise IndexError(i)
        return float(palavras[i][campo])

    # ---------------------------------------------------- resolver tempos
    eventos = []
    for k, ev in enumerate(plano.get("eventos", [])):
        ev = dict(ev)
        ev["id"] = ev.get("id") or f"{ev.get('tipo')}-{k}"
        tipo = ev.get("tipo")
        if tipo not in TIPOS:
            erros.append(f"{ev['id']}: tipo desconhecido '{tipo}'.")
            continue
        if tipo in SO_DE and SO_DE[tipo] != estilo:
            erros.append(f"{ev['id']}: '{tipo}' é do estilo {SO_DE[tipo]} e o vídeo está em {estilo}. "
                         "Um estilo por Reel: troque o componente ou o estilo.")
        if tipo == "zoom":
            ev.setdefault("modo", ZOOM_PADRAO[estilo])
        try:
            if "inicio" in ev:
                ini = float(ev["inicio"])
            elif "palavra" in ev:
                ini = t_palavra(ev["palavra"]) - ANTECIPA
            else:
                erros.append(f"{ev['id']}: falta 'inicio' ou 'palavra'.")
                continue

            for chave in ("itens", "linhas"):
                for j, it in enumerate(ev.get(chave, [])):
                    if "palavra" in it:
                        it["em"] = t_palavra(it["palavra"]) - ANTECIPA
                    elif "em" not in it:
                        it["em"] = ini + 0.45 + j * 0.9
                    it["em"] = max(float(it["em"]), ini)

            if "fim" in ev:
                fim = float(ev["fim"])
            elif "ate_palavra" in ev:
                fim = t_palavra(ev["ate_palavra"], "fim") + float(ev.get("segura", 0.35))
            elif "dur" in ev:
                fim = ini + float(ev["dur"])
            elif tipo == "lista":
                fim = max(it["em"] for it in ev.get("itens", [{"em": ini}])) + 1.6
            elif tipo == "comparacao":
                fim = max(it["em"] for it in ev.get("linhas", [{"em": ini}])) + 2.0
            elif tipo == "conta":
                fim = max(it["em"] for it in ev.get("linhas", [{"em": ini}])) + 2.4
            elif tipo == "cta":
                fim = dur
            else:
                fim = ini + DUR_PADRAO.get(tipo, 2.0)
        except IndexError as e:
            erros.append(f"{ev['id']}: índice de palavra {e} não existe na transcrição.")
            continue

        ini, fim = max(0.0, ini), min(dur, fim)
        if fim - ini < 0.3:
            erros.append(f"{ev['id']}: duração de {fim - ini:.2f}s é curta demais.")
        ev["inicio"], ev["fim"] = round(ini, 3), round(fim, 3)
        eventos.append(ev)
    eventos.sort(key=lambda e: e["inicio"])

    # ---------------------------------------------------- zoom nos cortes
    zoom_base = []
    zc = plano.get("zoom_cortes", {"ativo": True})
    cortes = []
    if plano.get("relatorio_cortes") and os.path.isfile(rel(plano["relatorio_cortes"])):
        r = json.load(open(rel(plano["relatorio_cortes"]), encoding="utf-8"))
        acc = 0.0
        for s, e in r.get("trechos_mantidos_s", [])[:-1]:
            acc += e - s
            cortes.append(round(acc, 3))
    if zc.get("ativo", True) and cortes:
        escala = float(zc.get("escala", 1.08))
        atual, ultimo, marcos = 1.0, -9.0, [0.0]
        niveis = [1.0]
        pontos = cortes + [dur]
        for i, c in enumerate(cortes):
            prox = pontos[i + 1]
            if prox - c >= 1.0 and c - ultimo >= 1.5:
                atual = escala if atual == 1.0 else 1.0
                ultimo = c
                marcos.append(c)
                niveis.append(atual)
        marcos.append(dur)
        for i in range(len(niveis)):
            if niveis[i] != 1.0:
                zoom_base.append({"ini": marcos[i], "fim": marcos[i + 1], "escala": niveis[i]})
    elif zc.get("ativo", True) and not cortes:
        notas.append("Sem relatório de cortes: zoom automático nos cortes desligado.")

    # ---------------------------------------------------- verificações
    def sobrepoe(a, b):
        return a["inicio"] < b["fim"] and b["inicio"] < a["fim"]

    grandes = [e for e in eventos if e["tipo"] in CARTOES | {"cta"}]
    # encostos curtos (saída de um invadindo a entrada do próximo) são aparados sozinhos
    for a, b in zip(grandes, grandes[1:]):
        invasao = a["fim"] - b["inicio"]
        if 0 < invasao <= 0.6 and b["inicio"] - a["inicio"] > 0.8:
            a["fim"] = round(b["inicio"] - 0.02, 3)
            notas.append(f"{a['id']} aparado para terminar quando {b['id']} entra.")
    for i, a in enumerate(grandes):
        for b in grandes[i + 1:]:
            if sobrepoe(a, b):
                erros.append(f"{a['id']} e {b['id']} aparecem ao mesmo tempo. Um cartão por vez.")
    for t in [e for e in eventos if e["tipo"] == "titulo"]:
        for c in grandes:
            if sobrepoe(t, c):
                avisos.append(f"{t['id']} divide a tela com {c['id']}. Prefira um de cada vez.")

    # ritmo: algo novo a cada 2 a 4 s (legenda não conta)
    novidades = sorted(set(
        [e["inicio"] for e in eventos] +
        [it["em"] for e in eventos for it in e.get("itens", []) + e.get("linhas", [])] +
        [z["ini"] for z in zoom_base] + [z["fim"] for z in zoom_base if z["fim"] < dur]
    ))
    pts = [0.0] + [n for n in novidades if 0 < n < dur] + [dur]
    maior = 0.0
    for a, b in zip(pts, pts[1:]):
        if b - a > maior:
            maior = b - a
        if b - a > 4.0:
            avisos.append(f"Nada novo entre {a:.1f}s e {b:.1f}s ({b - a:.1f}s). Regra: algo novo a cada 2 a 4 s.")
    for i in range(len(novidades)):
        janela = [n for n in novidades if novidades[i] <= n < novidades[i] + 1.0]
        if len(janela) > 3:
            avisos.append(f"{len(janela)} novidades em 1 s a partir de {novidades[i]:.1f}s. Tela poluída.")
            break

    # gancho
    gancho = [e for e in eventos if e["inicio"] <= 0.5 and e["tipo"] in {"titulo", "palavra", "numero", "carimbo"}]
    if not gancho:
        avisos.append("Gancho: nenhum título, palavra ou número até 0,5 s. Os 2 primeiros segundos decidem a retenção.")

    # limites de texto
    for e in eventos:
        tipo = e["tipo"]
        lim = LIMITE_TITULO[estilo] if tipo == "titulo" else LIMITES.get(tipo)
        if lim and n_palavras(e.get("texto")) > lim:
            erros.append(f"{e['id']}: {n_palavras(e.get('texto'))} palavras, limite {lim}"
                         f"{' no ' + estilo if tipo == 'titulo' else ''}.")
        if tipo == "palavra" and len(limpar(e.get("texto"))) > 12:
            erros.append(f"{e['id']}: palavra de impacto com mais de 12 letras não cabe.")
        elif tipo == "palavra" and estilo == "brutalista" and len(limpar(e.get("texto"))) > 9:
            avisos.append(f"{e['id']}: acima de 9 letras a Archivo Black encolhe para caber. Prefira palavra mais curta.")
        if tipo == "zoom" and estilo == "brutalista" and e.get("modo") == "suave":
            avisos.append(f"{e['id']}: zoom suave no Brutalista. O estilo pede corte seco.")
        if tipo == "emoji" and estilo == "blueprint":
            avisos.append(f"{e['id']}: emoji quebra a precisão do Blueprint. Use só se for essencial.")
        if e.get("etiqueta") and (n_palavras(e["etiqueta"]) > 4 or len(limpar(e["etiqueta"])) > 28):
            erros.append(f"{e['id']}: etiqueta '{e['etiqueta']}' longa. Até 4 palavras e 28 caracteres.")
        if tipo == "conta":
            lns = e.get("linhas", [])
            if not 2 <= len(lns) <= 5:
                erros.append(f"{e['id']}: conta com 2 a 5 linhas.")
            if len([ln for ln in lns if ln.get("resultado")]) != 1:
                avisos.append(f"{e['id']}: marque exatamente uma linha com \"resultado\": true "
                              "(é ela que ganha o traço de caneta).")
            for ln in lns:
                lim_c = 22 if "valor" in ln else (13 if ln.get("resultado") else 22)
                txt_ln = (str(ln.get("rotulo", "")) + " " + str(ln["valor"])) if "valor" in ln else ln.get("texto")
                if len(limpar(txt_ln)) > lim_c:
                    erros.append(f"{e['id']}: linha '{limpar(txt_ln)}' passa de {lim_c} caracteres (rótulo e valor somados).")
        if tipo == "carimbo" and (n_palavras(e.get("texto")) != 1 or len(limpar(e.get("texto"))) > 8):
            erros.append(f"{e['id']}: carimbo é uma palavra de até 8 letras (MITO, FATO, ERRO).")
        if tipo == "sticker" and n_palavras(e.get("texto")) > 4:
            erros.append(f"{e['id']}: sticker com mais de 4 palavras.")
        if tipo == "numero" and n_palavras(e.get("rotulo")) > 7:
            erros.append(f"{e['id']}: rótulo do número com mais de 7 palavras.")
        if tipo == "numero" and len(limpar(e.get("valor"))) > 9:
            avisos.append(f"{e['id']}: valor '{e.get('valor')}' longo. Acima de 9 caracteres pode não caber.")
        if tipo == "lista":
            if len(e.get("itens", [])) > 4:
                erros.append(f"{e['id']}: lista com mais de 4 itens.")
            for it in e.get("itens", []):
                if n_palavras(it.get("texto")) > 5:
                    erros.append(f"{e['id']}: item '{limpar(it.get('texto'))}' passa de 5 palavras.")
        if tipo == "comparacao" and not 2 <= len(e.get("linhas", [])) <= 3:
            erros.append(f"{e['id']}: comparação precisa de 2 ou 3 linhas.")
        if tipo in {"numero", "comparacao", "grafico", "conta"}:
            tem_aviso = any(a["tipo"] == "aviso" and sobrepoe(a, e) for a in eventos)
            if not e.get("fonte") and not tem_aviso:
                avisos.append(f"{e['id']}: número sem 'fonte' e sem aviso no mesmo trecho. "
                              "Dado real pede fonte e data. Exemplo pede 'Exemplo ilustrativo'.")
    emojis = [e for e in eventos if e["tipo"] == "emoji"]
    if len(emojis) > max(1, int(dur / 6)):
        avisos.append(f"{len(emojis)} emojis em {dur:.0f}s. Use no máximo 1 a cada 6 s.")
    titulos_centro = [e for e in eventos if e["tipo"] == "titulo" and e.get("y", 380) > 700]
    for e in titulos_centro:
        avisos.append(f"{e['id']}: título fora da área alta (320 a 700 px).")

    # compliance: sobreposições e fala
    textos = []
    for e in eventos:
        for campo in ("texto", "titulo", "topo", "rotulo", "valor", "final", "etiqueta"):
            if e.get(campo):
                textos.append((e["id"], limpar(e[campo])))
        for it in e.get("itens", []) + e.get("linhas", []):
            textos.append((e["id"], limpar(it.get("texto") or it.get("rotulo"))))
            if isinstance(it.get("valor"), str):
                textos.append((e["id"], limpar(it["valor"])))
    for idt, txt in textos:
        if SETA_DUPLA.search(str(txt)):
            erros.append(f"{idt}: seta dupla em '{txt}'. A seta dupla é da marca InvestSmart, não use.")
        for pat in PROIBIDOS:
            if re.search(pat, txt, re.I):
                erros.append(f"{idt}: termo proibido em tela ('{txt}'). Compliance.")
    fala = " ".join(w["texto"] for w in palavras)
    for pat in PROIBIDOS:
        m = re.search(pat, fala, re.I)
        if m:
            avisos.append(f"A fala contém '{m.group(0)}'. Não dá para editar a fala: avise o Lucas e "
                          "sugira regravar o trecho ou cortar.")

    duvidosas = [f"[{i}] {w['texto']}" for i, w in enumerate(palavras) if w.get("prob", 1) < 0.6]
    if duvidosas:
        notas.append("Palavras com baixa confiança na transcrição (conferir grafia): " + ", ".join(duvidosas[:30]))

    # ---------------------------------------------------- saída
    resolvido = {
        "video": video, "estilo": estilo, "fps": fps, "duracao": round(dur, 3),
        "foco": plano.get("foco", [540, 760]),
        "legenda": plano.get("legenda", {}),
        "palavras": [{"texto": w["texto"], "ini": float(w["ini"]), "fim": float(w["fim"])} for w in palavras],
        "zoom_base": zoom_base, "cortes": cortes,
        "eventos": eventos,
        "audio": plano.get("audio", {}),
        "novidades": novidades,
    }
    saida = os.path.join(base, "plano_resolvido.json")
    json.dump(resolvido, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"Vídeo: {os.path.basename(video)}  {dur:.1f}s  {len(palavras)} palavras  "
          f"{len(eventos)} eventos  {len(zoom_base)} trechos com zoom de corte  estilo {estilo}")
    print(f"Maior intervalo sem novidade: {maior:.1f}s")
    for titulo, lista in (("ERRO", erros), ("AVISO", avisos), ("NOTA", notas)):
        for m in lista:
            print(f"  {titulo}: {m}")
    if not (erros or avisos):
        print("  Tudo dentro das regras.")
    print(f"Plano resolvido: {saida}")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
