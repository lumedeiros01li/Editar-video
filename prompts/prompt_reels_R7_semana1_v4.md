# Reels R7 | Semana 1 (19 a 25/10) | @lucasmedeiros.ai | versão 4

Use a skill `reels-r7` para editar os Reels desta semana. Ela já tem todo o padrão R7: linha do tempo, visual Brutalista, área segura, regra do rosto, música, saídas e conferência. Este prompt só traz o que é desta semana e as regras que não podem ser quebradas.

## Como pedir

- "edita o QUI22-8": processa só esse ID.
- "edita todos": processa cada vídeo de `~/reels-r7/entrada/` cujo nome bate com um ID abaixo.
- Se eu mandar o vídeo como anexo, copie para `~/reels-r7/entrada/<ID>.mp4`.
- Se eu informar um tempo de início, use `--inicio`.
- Use este próprio arquivo como `--roteiros`.
- O QUA21-8 já foi entregue. Não refaça, a menos que eu peça.

## Regras que você NUNCA quebra

1. O texto dos roteiros é aprovado pelo compliance. Copie exatamente como está abaixo, com acentos, aspas e pontuação. Não reescreva, não resuma, não acrescente nenhuma frase.
2. O primeiro quadro do vídeo já mostra o balão 1. Os 3 primeiros segundos nunca ficam sem texto.
3. Não coloque logo, nome ou cor de XP ou InvestSmart. Não use seta dupla (chevron) em nenhuma forma.
4. Proibido: degradê, brilho, neon, sombra desfocada, canto arredondado, fade de opacidade, transição de dissolver, imagem de banco.
5. Os balões NUNCA cobrem meus olhos e minha boca.
6. Só crie os arquivos de saída listados na skill.
7. Pare e me pergunte antes de instalar qualquer dependência fora da lista da skill ou de apagar qualquer arquivo meu.

## Ajustes de layout desta versão (já estão na skill)

- Balões mais centralizados: o centro horizontal é x 520, e não mais 472. Eles podem passar um pouco das bordas laterais da área segura, mas nunca de x 930, contando a sombra.
- Pilha centralizada na vertical, no espaço entre y 270 e a chamada.
- Chamada "LEIA A LEGENDA 👇" menor (Archivo Black 44 px, padding 16 x 28, sombra roxa de 6 px) e mais baixa: centro em y 1500, podendo passar da base da área segura até y 1560, contando a sombra.
- Se o rosto bloquear a pilha, o passo 6 da skill está autorizado: balão 1 acima do rosto e balões 2 a 4 empilhados abaixo. Avise no resumo quando usar.

## Resposta

No fim, me responda só com:
- ID
- fonte e largura de cada balão, e fonte da chamada
- quais passos da regra do rosto foram aplicados
- se usou música da pasta ou sintetizada
- alertas: vídeo horizontal, quadro congelado, sobreposição na margem do rosto, chamada sem contraste com o fundo

Se o rosto bloquear mesmo com os 6 passos, não exporte. Me mostre o quadro com o problema e diga como reenquadrar.

## Roteiros da semana

Cada linha numerada é um balão. A chamada "LEIA A LEGENDA 👇" é igual em todos.

### SEG19-8 · Seu maior patrimônio não tem seguro
1. Você protege o carro, o celular e [[a casa]].
2. E [[a renda]] que paga tudo isso?
3. Ela é o seu [[maior patrimônio]] hoje.
4. E quase nunca tem [[cobertura]].
Capa: Seu maior patrimônio não tem seguro

### SEG19-19 · R$ 60 mil antes de herdar
1. Seu filho vai herdar. O estado [[cobra antes]].
2. ITCMD em MS: [[6%]] sobre a herança.
3. Em R$ 1 milhão, são [[R$ 60 mil]].
4. Fora [[inventário]], honorários e custas.
Aviso no balão 3: Exemplo ilustrativo.
Capa: R$ 60 mil antes de herdar

### TER20-8 · 1% ao mês: quanto sobra?
1. R$ 1 milhão rendendo [[1% ao mês]].
2. Parecem [[R$ 10 mil]] por mês.
3. Tira o IR de 15%: [[R$ 8,5 mil]].
4. Tira a inflação: sobram [[R$ 4,8 mil]].
Aviso no balão 1: Exemplo ilustrativo. Rentabilidade bruta, antes de impostos.
Capa: 1% ao mês: quanto sobra?

### TER20-19 · Sua família sabe?
1. Sua família sabe onde estão seus [[investimentos]]?
2. Banco, corretora, [[seguro]], previdência.
3. Não a senha. [[A existência.]]
4. Se ninguém sabe, [[ninguém aciona]].
Capa: Sua família sabe?

### QUA21-8 · Posso perder dinheiro?
1. “Eu posso [[perder dinheiro]] com isso?”
2. [[Pode.]] Todo investimento tem risco.
3. Até o título público [[oscila]] se você vender antes do vencimento.
4. A pergunta certa: quanto risco o seu [[objetivo]] aguenta?
Capa: Posso perder dinheiro?

### QUA21-19 · Quanto sobra para o dentista
1. Um dentista fatura [[R$ 40 mil]] por mês.
2. Impostos, equipe, aluguel e material: [[R$ 28 mil]].
3. Sobram [[R$ 12 mil]] para ele.
4. E se ele parar por [[6 meses]]?
Aviso no balão 1: Exemplo ilustrativo.
Capa: Quanto sobra para o dentista

### QUI22-8 · Seu seguro ainda serve?
1. “Tenho seguro, [[está tudo certo]].”
2. Quando foi a última vez que você [[leu a apólice]]?
3. O capital é de quando você [[ganhava menos]]?
4. O [[beneficiário]] ainda é quem você quer?
Capa: Seu seguro ainda serve?

### QUI22-19 · R$ 48 mil para herdar um imóvel
1. Imóvel de [[R$ 800 mil]] para os filhos.
2. ITCMD em MS: [[R$ 48 mil]].
3. Mais [[custas]] do inventário e honorários.
4. Tudo pago [[antes]] de o imóvel ir para o nome deles.
Aviso no balão 1: Exemplo ilustrativo.
Capa: R$ 48 mil para herdar um imóvel

### SEX23-8 · 3 meses de folha no caixa?
1. Sua empresa tem reserva para [[3 meses]] de folha?
2. Se não tem, [[o risco é seu]].
3. Se você parar, [[piora]].
4. Reserva da empresa e [[proteção do dono]] andam juntas.
Capa: 3 meses de folha no caixa?

### SEX23-19 · O seguro do cartão cobre o quê?
1. “Meu cartão tem [[seguro de vida]].”
2. Leia a apólice. Muitos cobrem [[só acidente]].
3. Morte por [[doença]] pode ficar de fora.
4. E a maioria das mortes no Brasil é [[por doença]].
Aviso no balão 4: Fonte: Ministério da Saúde, SIM/DATASUS.
Capa: O seguro do cartão cobre o quê?

### SAB24-8 · Quem cobre você?
1. Você é [[o seguro]] da sua família.
2. Paga escola, casa e [[plano de saúde]].
3. E [[quem cobre você]]?
4. Quase ninguém pensa nisso [[antes de precisar]].
Capa: Quem cobre você?

### SAB24-19 · Por que eu falo de seguro
1. “Por que um assessor fala tanto de [[seguro]]?”
2. Porque investimento leva [[anos]] para crescer.
3. E um imprevisto pode desfazer isso em [[meses]].
4. Por isso eu começo pela [[proteção]].
Capa: Por que eu falo de seguro

### DOM25-8 · Uma pergunta de domingo
1. [[Domingo]] em família.
2. Olhe para [[quem está na mesa]].
3. Se a sua renda parasse, o que mudaria [[para eles]]?
4. Responda [[só para você]].
Capa: Uma pergunta de domingo

### DOM25-19 · Ano que vem eu faço
1. “Ano que vem eu faço [[um seguro]].”
2. Com 1 ano a mais, o preço [[tende a subir]].
3. Se a saúde mudar, pode haver [[recusa ou exclusão]].
4. Adiar [[também é uma decisão]].
Capa: Ano que vem eu faço
