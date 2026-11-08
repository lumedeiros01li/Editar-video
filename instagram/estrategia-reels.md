# Estratégia de Reels @lucasmedeiros.ai

08/11/2026 · Dados do Apify (apify/instagram-scraper) · Skill do Instagram (robôs Viralização, Auditoria, Perfil, Roteiro e Planejador) + skill Roteiro de Reel Falado

## 1. Conclusão

O seu alcance não está só baixo. Ele está caindo, e a análise anterior não viu isso porque olhou só 10 dias.

| Período | Reels | Mediana de plays | Comentários por reel |
| --- | --- | --- | --- |
| Setembro | 12 | 331 | 3,75 |
| 01 a 18/10 | 3 | 378 | 1,0 |
| 19 a 25/10 | 15 | 172 | 0,3 |
| 26/10 a 05/11 | 32 | 88 | 0,4 |

Quatro coisas mudam o plano:

1. **Seus 4 maiores reels ficaram fora da análise anterior.** "O que custava 100 em 2000 custa 425 no Brasil e 111 no Japão" (2.474 plays, 23/10), ITCMD "Pouca gente calcula isso" (1.867, 04/09), "R$ 100 em 2000 viraram R$ 4.212 num ativo e R$ 593 em outro" (1.514, 24/10) e a eleição "51,8% a 48,2%" (1.326, 26/10). Nenhum é dilema. Três são comparação de números com contraste forte ou notícia quente.
2. **O seu formato é o oposto das referências.** A duração mediana dos reels de Bernardo, Pedro e Artur é 47 a 50 segundos, quase tudo falado. A sua é 7,2 segundos. A sua skill de roteiro falado (40 a 55 s, 7 estruturas) está pronta e quase não aparece no feed.
3. **O que você mais postou nas últimas 2 semanas é o que pior performa.** Personagem em terceira pessoa com pergunta A ou B: mediana de 54 plays. Legenda que cita lei ou artigo: 88, contra 135 sem lei. "Comenta CONTA": mediana de 66 e zero comentários em 14 reels.
4. **Os comentários de setembro vieram sem palavra-chave.** A chamada era "me chama no direct". O que gerou conversa foi tema com opinião (mesada, a frase do "nerd", "e se tal candidato ganhar?").

A mudança que move o número é trocar o formato principal: sair do reel de 7 segundos com música e entrar no falado de 40 a 50 segundos, com conta na tela e uma pergunta fácil de responder. Volume não resolve: você postou 2,3 por dia em setembro e 3 por dia agora, e o alcance caiu.

## 2. O que mudou em relação à análise anterior

| Ponto da análise anterior | Revisão com dados novos |
| --- | --- |
| "O problema é distribuição, não tema." | É distribuição e formato. O alcance caiu 4x em 2 meses com o mesmo tema. |
| Mediana de 78 plays | 164 em 62 reels desde setembro. 88 nos últimos 11 dias. A tendência importa mais que o ponto. |
| Melhores reels: 492, 255, 252 | Melhores: 2.474, 1.867, 1.514, 1.326. Todos antes de 26/10. |
| Fixar "10 mil de renda aos 60", "Seguro entre sócios" e "Escola" | Fixar os que provaram alcance e explicam a oferta (seção 6). |
| Manter 4 posts por dia | 2 falados por dia + 1 R7 de controle. O falado leva mais tempo para gravar, e volume não mostrou relação com alcance em nenhum dos 4 perfis. |
| "Dilema funciona nos três perfis" | Funciona no Pedro (2,5x) e no Bernardo (1,7x). No Artur o que funciona é preço do luxo (2,7x), que é outro formato. |

## 3. Método

- **Coleta:** 30 reels de cada referência (datasets da análise anterior) e uma coleta nova do seu perfil hoje: 90 posts desde setembro, 62 deles reels, mais um reel de 04/09 que só apareceu na aba de reels.
- **Métrica principal:** múltiplo de outlier = plays do reel ÷ mediana da própria conta. Acima de 3x é sinal, abaixo de 1,5x é dia normal (regra do robô Viralização). Isso evita comparar 38 mil seguidores com 170.
- **Classificação de formato:** o classificador automático da skill não reconheceu 110 dos 150 ganchos (finanças para alta renda não está no catálogo dele), então classifiquei à mão em 9 formatos. O script está em `dados/tag.py`.
- **Nota de gancho:** o `hookscore.py` da skill não separou os melhores dos piores neste lote (mediana 37 no terço de cima e 38 no de baixo). Usei a nota só para revisar tamanho e posição do número nos ganchos novos, não para prever alcance.
- **Limites:** só legenda e métricas públicas. Sem retenção, sem alcance de não seguidores, sem envios. Ganchos falados desconhecidos. As referências têm só 7 a 12 dias de dados.

## 4. Formatos que funcionam, medidos pelo múltiplo

Mediana do múltiplo de cada formato dentro de cada perfil (n = quantidade de reels):

| Formato | Bernardo | Pedro | Artur | Lucas |
| --- | --- | --- | --- | --- |
| A. Preço do luxo ("Cavalo de R$ 2 milhões custa R$ 50 mil por mês") | | | **2,7x** (n=8) | |
| B. Raio-x de personagem ("Custo de vida de um juiz que...") | | 1,3x (n=6) | **3,2x** (n=2) | 0,3x (n=5) |
| C. Dilema com decisão ("Pedro, tenho 67 anos... Empresto?") | 1,7x (n=4) | **2,5x** (n=2) | | |
| D. Comparativo histórico com contraste | | | | 1,4x (n=5), com 2 outliers de 15x e 9x |
| E. Notícia com número | | 0,9x (n=2) | 1,4x (n=1) | 1,7x (n=7) |
| F. Lista ("N erros", "3 títulos") | | 0,6x (n=5) | 1,2x (n=2) | 2,0x (n=5, todos de setembro) |
| G. Venda ("link na bio", "me chama") | 0,7x (n=5) | **0,4x** (n=7) | 0,3x (n=1) | |
| H. Entretenimento e opinião social | 1,0x (n=21) | | | |
| I. Ensino ou conta, outros | | 1,0x (n=8) | 0,6x (n=14) | 0,9x (n=40) |

Leitura:

- **Raio-x de personagem funciona falado e falha em 7 segundos.** É o mesmo tema nos três perfis. No Pedro e no Artur é um vídeo de 57 a 67 s com a conta na tela. No seu é texto de 7 s com música. A diferença de 0,3x para 1,3x a 3,2x é o que mais aponta para formato, e não tema.
- **Preço do luxo é o formato de maior alcance no nicho,** mas o Artur não liga o luxo ao serviço. A sua versão ganha se a conta for "quanto patrimônio precisa para bancar isso sem tocar no principal". É a sua marca (mostrar a conta) aplicada ao gancho que mais viaja.
- **Venda direta rende menos nos três perfis que a usam.** 12 reels de venda somados, todos abaixo de 1x.
- **Comparativo histórico é o seu formato próprio,** e é dele os seus dois maiores reels. Mas ele só funcionou quando o gancho tinha contraste ("425 no Brasil e 111 no Japão", "R$ 4.212 num ativo e R$ 593 em outro"). Quando o gancho era uma lista de nomes ("Nasdaq, Ibovespa, Nikkei, DAX e mais 4"), fez 67 plays.
- **Notícia quente funciona quando chega no dia.** A eleição saiu em 26/10, com o resultado de 25/10, e fez 1.326. Atenção: 23 a 26/10 foi a semana de eleição e circuit breaker, de interesse alto em finanças. Parte do alcance dos seus outliers vem do momento. Isso é um argumento a favor de ter um formato reativo pronto, não contra.

## 5. Avaliação por perfil

### @bernardocordeiroreal (Bernardo Cordeiro)

38.226 seguidores · 30 reels · mediana 5.627 plays (15% da base) · duração mediana 47 s · 29 de 30 falados

**O que ele faz.** 21 dos 30 reels são opinião social e comportamento (relacionamento, "vai estudar", "não seja um vagabundo"). Finanças aparece pouco e rende menos: LCI isenta 0,4x, "80 anos, 30 milhões" 0,6x. A legenda tem 1 a 6 palavras e não explica nada ("Não é segredo", "Qual sua opinião?").

**O que funciona.** Pergunta que divide o público com valor alto: "Faria esse acordo?" (11.786 plays, 84 comentários). Opinião assumida, sem meio-termo.

**O que não funciona.** "Me chama no direct" repetido 4 vezes em 90 minutos no dia 29/10: 2.694 a 4.651 plays, 0,7x. Reels longos e técnicos (238 s, 179 s) ficam nos piores.

**Para você copiar:** opinião assumida com pergunta de dois lados. **Para evitar:** polêmica de gênero, insulto ao espectador e qualquer frase que a sua compliance vete. O alcance dele vem em boa parte de tema fora do perfil de cliente.

| Alcance relativo | Série reconhecível | Gancho e legenda | Funil | Risco de compliance |
| --- | --- | --- | --- | --- |
| 6/10 | 4/10 | 6/10 | 5/10 | Alto |

### @compedrocosta (Pedro Costa)

2.162 seguidores · 30 reels · mediana 2.452 plays (113% da base, o mais eficiente) · duração mediana 48 s · 30 de 30 falados · ~4 reels por dia

**O que ele faz.** Séries com nome fixo no começo da frase: "Custo de vida de um(a) [profissão] que [erro]", "Carteira de um [perfil] com R$ X", "Pedro, sou [profissão], tenho R$ X... [decisão]?". A legenda tem sempre 3 linhas: gancho com valor, número de tensão, chamada.

**O que funciona.** Dilema do seguidor (2,5x): "Empresto R$ 1 milhão pro meu filho?" (7.839) e "Cirurgião, sócio do hospital, entro?" (4.290). Custo de vida com erro (1,4x mediana, chegando a 4.052). Notícia com número no dia ("O Copom decidiu: Selic mantida em 13,75%", 3.359).

**O que não funciona.** Toda chamada para o link da bio: 7 reels, mediana 0,4x. A mesma série "Carteira de" faz 2.984 quando termina em "O que você faria? Comenta" e 884 quando termina em "Quer uma avaliação? Link na bio". Listas também ficam abaixo (0,6x).

**Ponto fraco.** Alcance sem conversa: 47 comentários em 30 reels, 0,7 por 1.000 plays. O vídeo viaja para não seguidores, mas pouca gente fala com ele.

**Bio.** A melhor das quatro: público ("pra quem ganha bem"), diferencial ("sem comissão, só fee fixo") e oferta ("Diagnóstico grátis").

**Para você copiar:** séries com nome fixo, legenda de 3 linhas, chamada variada (comenta, manda pra alguém, guarda). **Para evitar:** "3 títulos do Tesouro que pagam mais de 15%" funciona (6.716), mas é produto com taxa. Na sua compliance isso pede revisão.

| Alcance relativo | Série reconhecível | Gancho e legenda | Funil | Risco de compliance |
| --- | --- | --- | --- | --- |
| 9/10 | 9/10 | 8/10 | 6/10 | Médio |

### @arturnegocios (Artur Oliveira)

2.707 seguidores · 28 reels · mediana 1.041 plays (38% da base) · duração mediana 50 s · quase tudo falado

**O que ele faz.** Metade do feed é preço do luxo e raio-x de profissional. A outra metade é motivacional ("Não existe a condição perfeita", "Não siga a manada") e opinião política.

**O que funciona.** Preço do luxo (2,7x): cavalo de hipismo (12.845, 85 comentários), helicóptero (10.275), marina (5.703). Raio-x de profissional: ortodontista com 4 clínicas (3.866, 27 comentários), clínica que perdeu processo (2.846). A legenda tem 2 linhas, um fato com número e "Comenta se você bancaria". O comentário vem porque a pergunta é pessoal e fácil.

**O que não funciona.** Motivacional e frase de efeito: 439 a 934 plays. FII (329). Venda (320). Política gera comentário (Bolsa Família contra Judiciário: 13 comentários), mas alcance médio e risco alto.

**Ponto fraco.** O luxo não liga ao serviço. Não há dado de que 12 mil plays de cavalo virem cliente. Bio genérica e link em tinyurl, que passa menos confiança que um domínio próprio ou Typebot.

**Para você copiar:** preço do luxo com a sua conta de patrimônio e o raio-x de profissional falado. **Para evitar:** motivacional, política e o luxo sem ponte para o seu nicho.

| Alcance relativo | Série reconhecível | Gancho e legenda | Funil | Risco de compliance |
| --- | --- | --- | --- | --- |
| 6/10 | 6/10 | 7/10 | 4/10 | Médio |

### @lucasmedeiros.ai (você)

170 seguidores · segue 386 · 62 reels desde setembro · mediana 164 (88 nos últimos 11 dias) · duração mediana 7,2 s

**O que funciona.**

- Comparativo com contraste forte: inflação de 7 países (2.474), 5 ativos desde 2000 em reais e dólar (1.514).
- Conta de imposto com dado que pouca gente conhece: ITCMD (1.867, 7 comentários). Foi falado, com áudio original, 8 s.
- Notícia no dia, com número: eleição (1.326).
- Primeira pessoa com cena de reunião, em setembro: "Em conversa de sucessão, a pergunta sobre os filhos quase sempre é quem vai receber" (439), "Fiz a conta que quase ninguém faz antes de prometer renda passiva. Achei cinco mentiras" (378), "Essa frase vende preguiça como se fosse esperteza" (340).

**O que não funciona.**

- Personagem em terceira pessoa com A ou B em 7 s: "Achar que a empresa é só sua" (50), "Sobrou R$ 0 em 8 de 12 meses" (53), "Afastado por 6 meses" (56). Mediana de 54.
- Explicação de lei: PGBL (54 e 66), ITCMD com LC 227 (69 e 71), seguro com Lei 15.040 (60).
- Simulação de juros: "Parar de investir 1 ano" (57), "R$ 1.000 por mês em 30 anos" (64).
- Legenda longa: 150 a 250 palavras, contra 2 a 3 linhas nas referências.

**Pontos fortes que as referências não têm.** Rigor de fonte e conta (nenhuma das três mostra premissa e fonte como você), aderência ao público de alta renda e empresário, e a menor exposição a risco de compliance dos quatro.

| Alcance relativo | Série reconhecível | Gancho e legenda | Funil | Risco de compliance |
| --- | --- | --- | --- | --- |
| 2/10 | 3/10 | 4/10 | 4/10 | Baixo |

Funil em 4: nenhum post fixado (confirmado na coleta: `isPinned` falso nos 90 posts), palavra-chave sem resposta e bio com superlativo.

## 6. Nota do perfil (rubrica de 12 itens do robô Perfil)

Pontuei só o que a coleta mostra. 26 dos 100 pontos dependem de print (destaques, grade, foto e stories).

| Item | Nota | Motivo |
| --- | --- | --- |
| Campo de nome | 5/12 | "Investidor profissional" é categoria regulada pela CVM e não é o que o cliente busca |
| Bio, linha 1 | 4/12 | Lista de serviços, sem dizer para quem |
| Resto da bio | 3/8 | "Maior Escritório XP do Brasil" sem fonte e "AI" ambíguo. "Comece pelo diagnóstico" é bom |
| Três fixados | 0/10 | Nada fixado |
| Link | 6/8 | Typebot de diagnóstico combina com a bio. Primeira tela não vista |
| @ | 4/6 | Legível, mas ".ai" lê como inteligência artificial |
| Categoria e contato | 5/6 | Conta profissional, categoria Finance |
| Atividade recente | 7/10 | Último post em 05/11. Poucos comentários para responder |
| Destaques, grade, foto, stories | não visto | Mande print |
| **Total verificável** | **34 de 74** | **46%** |

**Correções, em ordem:**

1. **Fixar 3 posts (5 min, maior ganho por minuto).**
   - Prova de alcance e de conta: "O que custava 100 em 2000 custa 425 no Brasil" (2.474).
   - Nicho de sucessão: ITCMD "Pouca gente calcula isso" (1.867, 7 comentários).
   - Como funciona a oferta: o carrossel "A primeira reunião comigo quase não tem investimento. Tem pergunta" (23/10).
2. **Nome (5 min).** `Lucas Medeiros | Assessor de Investimentos` ou `Lucas Medeiros | Planejamento Financeiro`. Os dois têm termos que o público busca e tiram "Investidor profissional".
3. **Bio (10 min).** Mantenho a V1 da análise anterior, que já resolve público, vínculo e chamada:
   ```
   Assessor de investimentos | InvestSmart XP
   Patrimônio, proteção e sucessão para dono de empresa e executivo
   Comece pelo diagnóstico 👇
   ```
   [REVISAR COMPLIANCE] na linha de identificação.
4. **@ (decisão sua).** Trocar ".ai" tem custo: link do Typebot, menções antigas, quem já decorou. Não é prioridade. Se trocar, faça junto com o Typebot.
5. **Seguindo 386.** As referências seguem 6 a 66. Não muda alcance, mas pesa na leitura de autoridade de quem chega.

## 7. A estratégia

### 7.1 Formato principal

**Falado de 40 a 50 segundos, gravado em blocos de 10 a 15 s, com a conta entrando na tela.** É o que os três perfis fazem e é o que a sua skill de roteiro já descreve. O R7 de 7 s vira teste de controle, não volume.

### 7.2 As 6 séries

Cada série tem um começo de frase fixo, para o público reconhecer, como o Pedro faz.

| Série | Começo fixo | Origem da evidência | Por semana |
| --- | --- | --- | --- |
| **1. Conta do personagem** | "Fatura X. Chuta quanto sobra." | Raio-x falado do Pedro (1,3x) e do Artur (3,2x). O seu em 7 s fez 0,3x | 3 |
| **2. Dilema de dois lados** | "X investidos. Você [decisão]?" | Pedro 2,5x, Bernardo 1,7x | 3 |
| **3. Preço em patrimônio** | "X milhões só pra manter [luxo]." | Artur 2,7x, com a sua conta de patrimônio | 2 |
| **4. Mesma base, destinos opostos** | "X em [ano] viraram A aqui e B ali." | Seus 2 maiores reels (15x e 9x) | 2 |
| **5. Notícia com número** | "[Fato]. Seus X rendem quanto agora?" | Sua eleição (8x), Copom do Pedro | 1 a 2, no dia do evento |
| **6. Ouço em reunião** | "Toda semana alguém me diz: '...'" | Seus reels de primeira pessoa de setembro (2x a 2,7x) | 2 |

Total: 13 a 14 falados por semana, 2 por dia. Mais 1 R7 por dia como controle (seção 7.5).

**Próximas datas para a série 5:** Copom em 8 e 9/12/2026 (último do ano). Grave a estrutura antes e preencha o número no dia.

### 7.3 Ganchos

- Até 8 palavras faladas. Número na primeira ou segunda palavra.
- Falado com número como se fala ("600 mil"). Na tela, com R$ ("R$ 600 mil").
- Fale com quem assiste ("seu", "você"). Na sua coleta, terceira pessoa ("Um casal...", "Um diretor...") fez mediana 54.
- Nada de lei, artigo ou número de processo no gancho nem na legenda. Fonte vai no rodapé do vídeo.

### 7.4 Legenda e chamada

**Legenda de 3 linhas,** como o Pedro:

```
[gancho com valor]
[número de tensão em uma frase]
[chamada única]
```

Fonte e aviso numa quarta linha curta, quando o caso pedir ("Simulação. Selic 13,75%, Copom de 04/11/2026.").

**Chamada pela resposta, não pela palavra-chave.** O comentário vem quando a pergunta é pessoal e fácil de responder:

| Em vez de | Use |
| --- | --- |
| "Comenta CONTA que eu te chamo no direct" | "Você quitaria? Comenta QUITO ou RENDE." |
| "Segue o perfil e comenta A ou B" | "Chuta nos comentários quanto sobra." |
| "Me chama no direct" | "Manda pra um sócio que precisa ver essa conta." |

Palavra-chave para o direct em 1 de cada 3 reels, só nos de conta pessoal (aposentadoria, seguro, sucessão), que é onde o direct vira reunião.

### 7.5 Teste pareado de 14 dias

O dado do seu perfil não separa duração de tema, porque os reels longos e curtos saíram em semanas diferentes. Para separar:

- Todo dia, 1 R7 de 7 s com o **mesmo tema** de um falado do dia anterior.
- Se a conta tiver a opção **Reels de teste** (o reel vai só para não seguidores primeiro), use nos R7. Assim o teste não ocupa o feed de quem já segue.
- Ao fim de 14 dias você tem ~14 pares. Se o falado ganhar em 10 ou mais, o R7 sai do calendário.

**Régua de decisão (dia 14):**

| Resultado da série | Decisão |
| --- | --- |
| Mediana acima de 250 plays (nível de setembro) | Mantém e ganha mais espaço |
| Entre 120 e 250 | Mantém e troca o gancho |
| Abaixo de 120 | Sai |

**Meça nos Insights, por reel:** retenção aos 3 segundos, % do alcance vindo de não seguidores, envios e seguidores ganhos. Mande prints dos 5 melhores e 5 piores no dia 14 para eu rodar a Auditoria. A regra do robô: reel com alcance e sem seguidor é problema de perfil. Reel sem alcance é problema de gancho.

### 7.6 Distribuição, além do post

Com 170 seguidores, o post sozinho não sai do lugar. Duas alavancas de baixo custo:

1. **Rodada de interação, 20 min por dia antes de postar** (robô Planejador): 5 contas grandes do seu público (médicos, dentistas, empresários do MS), 3 pares do seu tamanho e 2 possíveis clientes. Comentário de verdade, cedo, nunca venda.
2. **Collab com o contador e o advogado parceiros.** A sua compliance já pede validação deles em temas jurídicos e tributários. Fazer o reel em collab coloca o vídeo na base deles. É hipótese, não está nos dados.

### 7.7 Calendário da semana 1

| Dia | Falado 1 (manhã) | Falado 2 (noite) | R7 de controle |
| --- | --- | --- | --- |
| Seg | Dilema: quitar ou deixar rendendo | Conta do personagem: dentista com 2 clínicas | Tema do domingo |
| Ter | Ouço em reunião: "imóvel é o mais seguro" | Preço em patrimônio: barco | Quitar |
| Qua | Mesma base: 100 mil de 2010 em dólar | Dilema: [seu tema] | Dentista |
| Qui | Conta do personagem: [seu tema] | Ouço em reunião: [seu tema] | Imóvel |
| Sex | Dilema: [seu tema] | Preço em patrimônio: [seu tema] | Barco |
| Sáb | Mesma base: [seu tema] | Conta do personagem: [seu tema] | Dólar |
| Dom | Notícia da semana, se houver | Folga ou reserva | |

Os 6 primeiros roteiros estão prontos em `roteiros-semana-1.md`.

## 8. Compliance

Continua valendo tudo da análise anterior. Pontos novos desta estratégia:

- **Dilema** sempre como caso hipotético ("Imagina um médico..."), nunca "um cliente me perguntou" sem ser verdade. Na tela: "Simulação".
- **Preço do luxo** com custo real orçado, não chutado. Sem marca de barco, marina ou relógio.
- **Notícia** sem nome de candidato, partido ou autoridade, e sem previsão.
- **Série 6 ("ouço em reunião")** só com frase que você ouve de fato.
- O selo azul nos carrosséis, sem a conta ser verificada, continua pendente.

Filtro mínimo, não parecer jurídico. A palavra final é do compliance da InvestSmart e da XP.

## 9. Pendências

- [ ] Fixar os 3 posts e trocar nome e bio.
- [ ] Gravar os 6 roteiros da semana 1 e conferir os números marcados [CONFERIR].
- [ ] Ativar Reels de teste, se a conta tiver a opção.
- [ ] No dia 14 (22/11), mandar prints de Insights dos 5 melhores e 5 piores.
- [ ] Mandar print dos destaques, da grade e da primeira tela do Typebot.
- [ ] Preencher o aviso padrão aprovado pelo compliance.
- [ ] Confirmar se o diagnóstico é gratuito.

## 10. Dados

| Arquivo | O que tem |
| --- | --- |
| `dados/lucas_posts_2026-11-08.json` | 90 posts seus desde setembro (Apify, dataset InPWE3gpxdRbvGAjH) |
| `dados/refs.py` | 88 reels das 3 referências (datasets ZfSsppQF53UrOaYJZ, OSPPMMLOgvgSHBB5r, V4VvGSc5ajgfbp3CS) |
| `dados/tag.py` | Classificação por formato e múltiplo. Rode com `python3 tag.py` de dentro de `dados/` |
| `dados/coletados.tsv` | Entrada do `swipe.py` da skill |
| `dados/virais.md` | Saída do `swipe.py`, ranking dos 150 reels por múltiplo |

Fontes externas usadas nos roteiros: [calendário do Copom 2026 (B3 Bora Investir)](https://borainvestir.b3.com.br/noticias/copom-tera-8-reunioes-em-2026-veja-calendario-e-projecao-para-a-selic/), [rentabilidade do aluguel FipeZAP](https://www.agazeta.com.br/hub-imobi/inovacao/aluguel-residencial-tem-leve-alta-em-outubro-e-fica-acima-da-inflacao-1122), [dólar médio de 2010 (numerando, dados do BCB)](https://www.numerando.com.br/indices/dolar/2010). As três são secundárias. Confirme na fonte primária antes de gravar.
