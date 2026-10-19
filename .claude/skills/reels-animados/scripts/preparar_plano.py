#!/usr/bin/env python3
"""
Resolve o plano do Reel animado e verifica as regras.

Uso:
    python preparar_plano.py plano.json

- Âncoras por texto ("ancora": "mil reais") viram tempos da fala.
- Inícios de cena e de elemento caem na grade de semicolcheias da trilha (beats.json).
- Resolve o estilo (blueprint ou brutalista). Sem "estilo" no plano, escolhe pelo conteúdo.
- Gera plano_resolvido.json e beats.json ao lado do plano.
Sai com código 1 se houver ERRO.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import unicodedata

ANTECIPA = 0.06
TIPOS = {"frase", "numero", "icone", "icones", "personagem", "comparacao", "grafico", "moedas",
         "lista", "linha_tempo", "rosca", "cta", "aviso", "conta", "carimbo", "sticker"}
ESTILOS = {"blueprint", "brutalista"}
# componente exclusivo de um estilo: usar no outro mistura as linguagens
SO_DE = {"carimbo": "brutalista", "sticker": "brutalista"}
FUNDOS = {"blueprint": {"papel"}, "brutalista": {"cinza", "preto", "roxo"}}
FUNDO_PADRAO = {"blueprint": "papel", "brutalista": "cinza"}
TRANSICOES = {"blueprint": {"corte", "cortina", "lateral", "empurra"}, "brutalista": {"corte", "bloco"}}
TRILHA = {"blueprint": "suave", "brutalista": "pulso"}
LIMITE_FRASE = {"g": 6, "m": 10, "p": 16}
LIMITE_TITULO_BRUTALISTA = 8
SETA_DUPLA = re.compile(r"»|«|≫|≪|>>|<<|›\s*›|‹\s*‹")
# palavras da fala que puxam cada estilo
PISTAS = {
    "blueprint": r"\b(quanto|conta|calcul\w*|simula\w*|por m[eê]s|juros|rend\w*|precis\w*|multiplic\w*|soma|dividi\w*)\b",
    "brutalista": r"\b(mito|fato|verdade|mentira|erro|errad\w*|cuidado|alerta|lei|regra|proibid\w*|nunca|golpe)\b",
}
PROIBIDOS = [
    r"blindagem", r"garantid[oa]s?", r"sem risco", r"risco zero", r"renda certa",
    r"dobr\w* (o |seu |teu )?dinheiro", r"lucro f[aá]cil", r"retorno certo",
    r"enriquec\w* r[aá]pido", r"(rentabilidade|retorno) garantid",
]


def norm(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)


def limpar(s):
    return re.sub(r"\*\*|\[\[|\]\]", "", str(s or ""))


def n_palavras(s):
    # "R$ 10" conta como uma palavra: o símbolo colado ao número é lido junto
    return len(re.sub(r"R\$\s+(?=\d)", "R$", limpar(s)).split())


def duracao(path):
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
    rel = lambda p: p if os.path.isabs(p) else os.path.join(base, p)  # noqa: E731
    plano = json.load(open(caminho, encoding="utf-8"))
    erros, avisos, notas = [], [], []

    voz = rel(plano["audio"])
    if not os.path.isfile(voz):
        sys.exit(f"ERRO: áudio não encontrado: {voz}")
    dur_voz = duracao(voz)
    dur = round(dur_voz + float(plano.get("cauda", 1.2)), 3)
    fps = float(plano.get("fps", 30))

    trans = json.load(open(rel(plano["transcricao"]), encoding="utf-8"))
    palavras = trans["palavras"] if isinstance(trans, dict) else trans
    toks = [(i, norm(w["texto"])) for i, w in enumerate(palavras) if norm(w["texto"])]

    # ---------------------------------------------------- estilo
    estilo = plano.get("estilo")
    fala_txt = " ".join(w["texto"] for w in palavras).lower()
    tipos_plano = [e.get("tipo") for c in plano.get("cenas", []) for e in c.get("elementos", [])]
    if estilo is None:
        pts = {"blueprint": 0.0, "brutalista": 0.0}
        motivos = {"blueprint": [], "brutalista": []}
        for tp in tipos_plano:
            if tp in {"conta", "grafico", "comparacao", "moedas", "rosca", "numero"}:
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
                     f"ponha \"estilo\" no plano.")
    if estilo not in ESTILOS:
        erros.append(f"estilo '{estilo}' não existe. Use blueprint ou brutalista.")
        estilo = "blueprint"

    musica = dict(plano.get("musica", {}))
    musica.setdefault("ativa", True)
    musica.setdefault("estilo", TRILHA[estilo])
    bpm = float(musica.get("bpm", 96))
    passo = 60.0 / bpm / 4  # semicolcheia

    def grade(t):
        if not musica["ativa"] or t <= 0:
            return t
        return round(round(t / passo) * passo, 3)

    def achar(texto, desde=0):
        alvo = [norm(x) for x in limpar(texto).split() if norm(x)]
        if not alvo:
            return None
        pos = [k for k, (i, _) in enumerate(toks) if i >= desde]
        if not pos:
            return None
        k0 = pos[0]
        n = len(alvo)
        for k in range(k0, len(toks) - n + 1):
            if [tk for _, tk in toks[k:k + n]] == alvo:
                return toks[k][0]
        melhor, idx = 0.0, None
        a = " ".join(alvo)
        for k in range(k0, len(toks) - n + 1):
            r = difflib.SequenceMatcher(None, a, " ".join(tk for _, tk in toks[k:k + n])).ratio()
            if r > melhor:
                melhor, idx = r, toks[k][0]
        if melhor >= 0.78:
            notas.append(f"Âncora '{texto}' achada por aproximação ({melhor:.0%}): "
                         f"'{palavras[idx]['texto']}...'. Confira.")
            return idx
        return None

    def tempo_inicio(obj, desde, padrao, rotulo):
        if "inicio" in obj:
            return float(obj["inicio"]), desde
        if "palavra" in obj:
            i = int(obj["palavra"])
            return float(palavras[i]["ini"]) - ANTECIPA, i
        if "ancora" in obj:
            i = achar(obj["ancora"], desde)
            if i is None:
                erros.append(f"{rotulo}: âncora '{obj['ancora']}' não aparece na fala depois da "
                             f"palavra {desde}. O Lucas pode ter falado diferente do roteiro: copie o trecho "
                             "de transcricao.txt.")
                return padrao, desde
            return float(palavras[i]["ini"]) - ANTECIPA, i
        return padrao, desde

    # ---------------------------------------------------- cenas
    cenas, cursor = [], 0
    for k, c in enumerate(plano.get("cenas", [])):
        c = dict(c)
        c["id"] = c.get("id") or f"c{k + 1}"
        if k == 0:
            ini, idx = 0.0, 0
            if "ancora" in c:
                achado = achar(c["ancora"], 0)
                idx = achado if achado is not None else 0
        else:
            ini, idx = tempo_inicio(c, cursor, None, c["id"])
            if ini is None:
                continue
        c["inicio"], c["_idx"] = grade(max(0.0, ini)), idx
        cursor = idx
        c.setdefault("fundo", FUNDO_PADRAO[estilo])
        if c["fundo"] not in FUNDOS[estilo]:
            erros.append(f"{c['id']}: fundo '{c['fundo']}' não existe no estilo {estilo} "
                         f"({', '.join(sorted(FUNDOS[estilo]))}).")
        if c.get("transicao", "corte") not in TRANSICOES[estilo]:
            erros.append(f"{c['id']}: transição '{c.get('transicao')}' não existe no estilo {estilo} "
                         f"({', '.join(sorted(TRANSICOES[estilo]))}).")
        cenas.append(c)
    for a, b in zip(cenas, cenas[1:]):
        a["fim"] = b["inicio"]
    if cenas:
        cenas[-1]["fim"] = dur

    # ---------------------------------------------------- elementos
    icones_validos = set()
    ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "engine", "icones.js")
    if os.path.isfile(ico):
        icones_validos = set(re.findall(r"^\s*(\w+):", open(ico, encoding="utf-8").read(), re.M))

    novidades = []
    for c in cenas:
        novidades.append(c["inicio"])
        elems = []
        for j, e in enumerate(c.get("elementos", [])):
            e = dict(e)
            e["id"] = e.get("id") or f"{c['id']}-{e.get('tipo')}-{j}"
            if e.get("tipo") not in TIPOS:
                erros.append(f"{e['id']}: tipo desconhecido '{e.get('tipo')}'.")
                continue
            if e.get("tipo") in SO_DE and SO_DE[e["tipo"]] != estilo:
                erros.append(f"{e['id']}: '{e['tipo']}' é do estilo {SO_DE[e['tipo']]} e o vídeo está em {estilo}. "
                             "Um estilo por Reel: troque o componente ou o estilo.")
            padrao = c["inicio"] + (0.12 if c.get("transicao", "corte") == "corte" else 0.2)
            ini, idx = tempo_inicio(e, c["_idx"], padrao, e["id"])
            ini = grade(max(ini, c["inicio"]))
            for chave in ("itens", "linhas", "colunas", "marcos", "segmentos"):
                ultimo = idx
                for q, it in enumerate(e.get(chave, [])):
                    if any(x in it for x in ("ancora", "palavra", "inicio")):
                        t_it, ultimo = tempo_inicio(it, ultimo, ini + 0.4 + q * 0.8, f"{e['id']} item {q + 1}")
                    else:
                        t_it = ini + 0.4 + q * 0.8
                    it["em"] = grade(max(t_it, ini))
                    novidades.append(it["em"])
            if e["tipo"] == "personagem" and "balao_ancora" in e:
                tb, _ = tempo_inicio({"ancora": e["balao_ancora"]}, idx, ini + 0.6, e["id"] + " balão")
                e["balao_em"] = grade(max(tb, ini + 0.3))
            if e["tipo"] == "frase" and e.get("sincronizar"):
                # cada palavra da frase entra quando é dita
                ft = [norm(x) for x in limpar(e["texto"]).split()]
                tempos, k = [], next((q for q, (i, _) in enumerate(toks) if i >= idx), len(toks))
                for tk in ft:
                    achou = None
                    for q in range(k, min(k + 6, len(toks))):
                        if toks[q][1] == tk:
                            achou = q
                            break
                    if achou is not None:
                        tempos.append(round(float(palavras[toks[achou][0]]["ini"]) - ANTECIPA, 3))
                        k = achou + 1
                    else:
                        tempos.append(round((tempos[-1] + 0.12) if tempos else ini, 3))
                e["tempos"] = [max(t, ini) for t in tempos]
            if "fim" in e:
                fim = float(e["fim"])
            elif "ate_ancora" in e:
                i = achar(e["ate_ancora"], idx)
                if i is None:
                    erros.append(f"{e['id']}: 'ate_ancora' '{e['ate_ancora']}' não encontrada.")
                    fim = c["fim"]
                else:
                    fim = float(palavras[i]["fim"]) + float(e.get("segura_s", 0.35))
            elif "dur" in e:
                fim = ini + float(e["dur"])
            else:
                fim = c["fim"]
            if fim >= c["fim"] - 1e-6:
                fim, e["segura"] = c["fim"], True
            e["inicio"], e["fim"] = round(ini, 3), round(fim, 3)
            if e["fim"] - e["inicio"] < 0.3:
                erros.append(f"{e['id']}: fica só {e['fim'] - e['inicio']:.2f}s na tela.")
            novidades.append(e["inicio"])
            # quando algo aparece de fato: frase sincronizada espera a primeira palavra,
            # contêiner sem título espera o primeiro item
            vis = e["inicio"]
            if e.get("tempos"):
                vis = min(e["tempos"])
            itens_e = [it["em"] for k2 in ("itens", "linhas", "colunas", "marcos", "segmentos")
                       for it in e.get(k2, [])]
            if itens_e and not e.get("titulo") and e["tipo"] != "rosca":
                vis = min(itens_e)
            e["_visivel"] = vis
            elems.append(e)

            # limites e conferências por tipo
            tipo = e["tipo"]
            if tipo == "frase":
                lim = LIMITE_FRASE.get(e.get("tamanho", "m"), 10)
                if estilo == "brutalista":
                    lim = min(lim, LIMITE_TITULO_BRUTALISTA)
                if n_palavras(e.get("texto")) > lim:
                    erros.append(f"{e['id']}: frase tamanho {e.get('tamanho', 'm')} com "
                                 f"{n_palavras(e.get('texto'))} palavras (limite {lim} no {estilo}).")
            if e.get("etiqueta") and (n_palavras(e["etiqueta"]) > 4 or len(limpar(e["etiqueta"])) > 28):
                erros.append(f"{e['id']}: etiqueta '{e['etiqueta']}' longa. Até 4 palavras e 28 caracteres.")
            if tipo == "conta":
                lns = e.get("linhas", [])
                if not 2 <= len(lns) <= 5:
                    erros.append(f"{e['id']}: conta com 2 a 5 linhas.")
                res = [ln for ln in lns if ln.get("resultado")]
                if len(res) != 1:
                    avisos.append(f"{e['id']}: marque exatamente uma linha com \"resultado\": true "
                                  "(é ela que ganha o traço de caneta).")
                for ln in lns:
                    lim = 26 if "valor" in ln else (16 if ln.get("resultado") else 24)
                    txt_ln = (str(ln.get("rotulo", "")) + " " + str(ln["valor"])) if "valor" in ln else ln.get("texto")
                    if len(limpar(txt_ln)) > lim:
                        erros.append(f"{e['id']}: linha '{limpar(txt_ln)}' passa de {lim} caracteres (rótulo e valor somados).")
            if tipo == "carimbo" and (n_palavras(e.get("texto")) != 1 or len(limpar(e.get("texto"))) > 8):
                erros.append(f"{e['id']}: carimbo é uma palavra de até 8 letras (MITO, FATO, ERRO).")
            if tipo == "sticker" and n_palavras(e.get("texto")) > 4:
                erros.append(f"{e['id']}: sticker com mais de 4 palavras.")
            if tipo == "numero" and len(limpar(e.get("valor"))) > 8:
                avisos.append(f"{e['id']}: valor '{e.get('valor')}' longo. Acima de 8 caracteres o motor reduz a fonte.")
            if tipo in {"icone"} and e.get("icone") not in icones_validos:
                erros.append(f"{e['id']}: ícone '{e.get('icone')}' não existe. Opções: {', '.join(sorted(icones_validos))}.")
            if tipo == "icones":
                if not 2 <= len(e.get("itens", [])) <= 4:
                    erros.append(f"{e['id']}: use 2 a 4 ícones.")
                for it in e.get("itens", []):
                    if it.get("icone") not in icones_validos:
                        erros.append(f"{e['id']}: ícone '{it.get('icone')}' não existe.")
            if tipo == "lista" and len(e.get("itens", [])) > 4:
                erros.append(f"{e['id']}: lista com mais de 4 itens.")
            if tipo == "moedas" and not 1 <= len(e.get("colunas", [])) <= 3:
                erros.append(f"{e['id']}: use 1 a 3 pilhas de moedas.")
            if tipo == "linha_tempo" and len(e.get("marcos", [])) > 4:
                erros.append(f"{e['id']}: linha do tempo com mais de 4 marcos.")
            if tipo == "rosca" and not 2 <= len(e.get("segmentos", [])) <= 4:
                erros.append(f"{e['id']}: rosca com 2 a 4 fatias.")
            if tipo == "cta" and n_palavras(e.get("texto")) > 8:
                erros.append(f"{e['id']}: CTA com mais de 8 palavras.")
        c["elementos"] = elems
        primeiro = min((e["_visivel"] for e in elems), default=None)
        if primeiro is None:
            avisos.append(f"{c['id']}: cena sem elementos, só fundo e legenda.")
        elif primeiro - c["inicio"] > 0.6:
            avisos.append(f"{c['id']}: tela vazia por {primeiro - c['inicio']:.1f}s no começo da cena. "
                          "Ancore a cena mais perto do primeiro elemento ou adiante um elemento.")

        # um assunto por vez: no máximo 2 elementos principais juntos
        principais = [e for e in elems if e["tipo"] not in {"aviso", "sticker"}]
        for e in principais:
            juntos = [o for o in principais if o["inicio"] < e["fim"] and e["inicio"] < o["fim"]]
            if len(juntos) > 2:
                avisos.append(f"{c['id']}: {len(juntos)} elementos na tela ao mesmo tempo. No máximo 2.")
                break
        numericos = [e for e in elems if e["tipo"] in {"numero", "comparacao", "grafico", "moedas", "rosca", "conta"}]
        for e in numericos:
            if not e.get("fonte") and not any(o["tipo"] == "aviso" for o in elems):
                avisos.append(f"{e['id']}: número sem 'fonte' e sem aviso na cena. Dado real pede fonte e data, "
                              "exemplo pede 'Exemplo ilustrativo, não é promessa de resultado.'")

    # ---------------------------------------------------- ritmo e estrutura
    for c in cenas:
        d = c["fim"] - c["inicio"]
        if d < 1.2 and c is not cenas[-1]:
            avisos.append(f"{c['id']}: cena de {d:.1f}s. Menos de 1,2 s não dá tempo de ler.")
    novidades = sorted(set(round(n, 3) for n in novidades))
    pts = [0.0] + [n for n in novidades if 0 < n < dur_voz] + [dur_voz]
    maior = max((b - a for a, b in zip(pts, pts[1:])), default=0)
    for a, b in zip(pts, pts[1:]):
        if b - a > 4.0:
            avisos.append(f"Nada novo entre {a:.1f}s e {b:.1f}s. Regra: algo novo a cada 2 a 4 s.")
    if cenas and not any(e["_visivel"] <= 0.3 for e in cenas[0]["elementos"]):
        avisos.append("Gancho: nada aparece na tela até 0,3 s (frase sincronizada espera a fala). "
                      "Coloque um elemento visível no quadro 0.")
    if not any(e["tipo"] == "cta" for c in cenas[-1:] for e in c["elementos"]):
        avisos.append("A última cena não tem CTA.")
    seq = [c.get("transicao", "corte") for c in cenas[1:]]
    for k in range(len(seq) - 2):
        if seq[k] == seq[k + 1] == seq[k + 2] and seq[k] != "corte":
            avisos.append(f"Transição '{seq[k]}' 3 vezes seguidas a partir de {cenas[k + 1]['id']}. Varie.")
            break
    fundos = [c.get("fundo") for c in cenas]
    for k in range(len(fundos) - 3):
        if estilo == "brutalista" and len(set(fundos[k:k + 4])) == 1:
            avisos.append(f"Fundo '{fundos[k]}' em 4 cenas seguidas a partir de {cenas[k]['id']}. Alterne.")
            break
    if dur > 90:
        avisos.append(f"{dur:.0f}s de vídeo. Acima de 90 s a retenção cai muito: corte o roteiro.")

    # ---------------------------------------------------- compliance
    for c in cenas:
        for e in c["elementos"]:
            campos = [e.get(x) for x in ("texto", "titulo", "topo", "rotulo", "valor", "final", "sub",
                                          "nome", "descricao", "balao", "centro", "etiqueta")]
            for chave in ("itens", "linhas", "colunas", "marcos", "segmentos"):
                for it in e.get(chave, []):
                    campos += [it.get("texto"), it.get("rotulo"), it.get("quando"), it.get("valor") if isinstance(it.get("valor"), str) else None]
            for txt in filter(None, campos):
                if SETA_DUPLA.search(str(txt)):
                    erros.append(f"{e['id']}: seta dupla em '{limpar(txt)}'. A seta dupla é da marca InvestSmart, não use.")
                for pat in PROIBIDOS:
                    if re.search(pat, limpar(txt), re.I):
                        erros.append(f"{e['id']}: termo proibido em tela ('{limpar(txt)}').")
    fala = " ".join(w["texto"] for w in palavras)
    for pat in PROIBIDOS:
        m = re.search(pat, fala, re.I)
        if m:
            avisos.append(f"A fala contém '{m.group(0)}'. Avise o Lucas: regravar o trecho.")

    # ---------------------------------------------------- saída
    for c in cenas:
        c.pop("_idx", None)
        for e in c["elementos"]:
            e.pop("_visivel", None)
    batidas = [round(k * 4 * passo, 3) for k in range(int(dur / (4 * passo)) + 2)]
    beats = {"bpm": bpm, "semicolcheia": round(passo, 5), "batidas": batidas,
             "compassos": batidas[::4], "acertos": novidades}
    json.dump(beats, open(os.path.join(base, "beats.json"), "w", encoding="utf-8"), indent=1)
    resolvido = {
        "audio": voz, "estilo": estilo, "fps": fps, "duracao": dur, "duracao_voz": round(dur_voz, 3),
        "legenda": plano.get("legenda", {}), "musica": musica,
        "sfx": plano.get("sfx", True), "volume_sfx": plano.get("volume_sfx", 0),
        "palavras": [{"texto": w["texto"], "ini": float(w["ini"]), "fim": float(w["fim"])} for w in palavras],
        "cenas": cenas,
    }
    saida = os.path.join(base, "plano_resolvido.json")
    json.dump(resolvido, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    n_el = sum(len(c["elementos"]) for c in cenas)
    print(f"Áudio: {os.path.basename(voz)}  {dur_voz:.1f}s de fala + cauda = {dur:.1f}s  "
          f"{len(cenas)} cenas  {n_el} elementos  estilo {estilo}  trilha {musica['estilo']} {bpm:.0f} bpm")
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
