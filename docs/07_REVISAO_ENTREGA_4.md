# 07 — Revisão técnica da Entrega 4

## Ponto de partida da revisão

Uma revisão mais ampla foi realizada a partir do pacote **Entrega 4 - Finaxis 2.0**. A ideia foi identificar riscos e pontos de melhoria antes de continuar alterando o sistema.

## Principais observações registradas

- O pacote continha um ambiente virtual muito grande, que não precisava ser distribuído.
- Havia elementos duplicados na barra lateral, incluindo contagem de notificações e botão de saída.
- O CSS aplicava uma aparência escura de forma ampla, mesmo quando o tema claro era escolhido.
- A seleção de moeda não era refletida corretamente em toda a formatação.
- Os relatórios precisavam de filtros adicionais e exportações mais completas.
- O controle de tentativas de login precisava de correção após o fim do bloqueio.
- O processamento de recorrências atrasadas poderia executar um volume excessivo de trabalho.
- A restauração de backup precisava de validações mais rigorosas.
- Os bancos de dados incluídos no material de trabalho continham informações privadas e não deveriam seguir nos pacotes distribuídos.

## Testes do ponto de partida

Na revisão inicial, os 13 testes existentes passaram e os arquivos principais foram compilados sem erros.

## Como essa revisão foi usada

As observações serviram como roteiro para as seis etapas de correção descritas nos documentos seguintes.
