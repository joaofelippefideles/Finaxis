# Finaxis — Correções de interface e lançamentos duplicados

## Objetivo
Corrigir os problemas visuais observados nas capturas de tela e impedir que um único envio de receita/despesa gere vários lançamentos.

## Correções implementadas

### 1. Envio único de receita e despesa
- O formulário de nova movimentação passou a usar `clear_on_submit=True`.
- Cada envio recebe uma chave de idempotência mantida na sessão.
- O banco registra a chave associada ao lançamento em `transaction_submissions`, com restrição única por usuário.
- Se o mesmo envio for repetido pelo navegador, Streamlit ou por uma repetição de requisição, o banco retorna o lançamento já criado em vez de inserir outro.
- Após um envio confirmado, a interface gera uma nova chave para o próximo lançamento e limpa os campos.
- Envios intencionais diferentes continuam permitidos, mesmo com mesmo valor, data e descrição, pois recebem chaves diferentes.

### 2. CSS e temas
- Reforçadas as regras do tema escuro para alertas, tabelas, cabeçalho, menus, seletores e áreas dos gráficos.
- Ajustado o contraste de mensagens de informação no tema escuro, que apareciam com fundo claro e texto pouco legível.
- Mantidas regras específicas para o tema claro.
- Melhorada a consistência visual entre cartões, gráficos, formulários e navegação.

### 3. Avisos do Streamlit
- Substituídos os usos de `use_container_width=True/False` por `width="stretch"` / `width="content"`, conforme a orientação da versão instalada.
- A busca estática no código confirmou zero ocorrências restantes de `use_container_width`.

## Validação executada
- **27 testes automatizados aprovados.**
- `py_compile app.py database.py`: aprovado.
- Teste de reenvio com a mesma chave: um único lançamento criado.
- Teste de duas chaves diferentes: dois lançamentos intencionais continuam permitidos.
- Integridade do pacote ZIP: verificada.
- Nenhum banco financeiro pessoal foi incluído no pacote.

## Observação sobre a validação visual
As regras CSS foram revisadas e ajustadas com base nas capturas enviadas. Os testes automatizados e a compilação foram executados, mas não foi possível interagir no navegador deste ambiente para confirmar visualmente cada página. Recomenda-se validar localmente os temas Claro/Escuro e fazer um teste real de envio único.

## Instalação da atualização
1. Faça uma cópia da pasta atual do Finaxis e do banco `data/finaxis_v2.db`.
2. Extraia este ZIP em uma pasta nova.
3. Preserve seu banco atual: não substitua `data/finaxis_v2.db` por um banco vazio do pacote.
4. Na raiz do projeto, execute `pip install -r requirements.txt`.
5. Inicie com `streamlit run app.py`.

A nova tabela de idempotência é criada automaticamente pelo `db.init_db()` ao iniciar a versão atualizada.
