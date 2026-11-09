# Finaxis — Ajuste do tema escuro

## Problemas observados
Nas capturas enviadas, algumas tabelas continuavam com aparência clara e diversos botões/alertas tinham texto com contraste insuficiente no tema escuro.

## Correções
1. Criada a função `show_dataframe`, que aplica explicitamente `theme="dark"` às tabelas no tema escuro e `theme="light"` no tema claro.
2. Reforçado o CSS para tabelas nativas, componentes de DataFrame, cabeçalhos, células e bordas.
3. Padronizados botões comuns, botões de formulário, downloads e links, incluindo hover, foco e estado desabilitado.
4. Ajustados campos, menus suspensos, listas de seleção, abas, expansores e alertas.
5. Preservado o tema claro com estilos próprios.
6. Mantidos o inicializador de um clique e as proteções de lançamentos duplicados.

## Validação
- 27 testes automatizados aprovados.
- `py_compile app.py database.py` aprovado.
- ZIP validado.
- Nenhum banco de dados pessoal foi incluído.

## Limitação
A correção foi feita a partir das capturas e validada por testes e compilação. A confirmação visual final deve ser feita no navegador do usuário, alternando Claro/Escuro e conferindo tabelas e botões em várias páginas.

## Instalação
1. Faça backup da pasta atual e de `data/finaxis_v2.db`.
2. Extraia o ZIP atualizado em uma pasta separada.
3. Copie o banco atual para a pasta `data` da nova instalação, sem sobrescrever o original.
4. Execute `INICIAR_FINAXIS.bat` na raiz do projeto.
