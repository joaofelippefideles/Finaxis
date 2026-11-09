# Auditoria da documentação — Finaxis

Data da auditoria: 09/11/2026

## 1. Escopo e método

- Pasta analisada: `docs/`.
- Subpastas encontradas: nenhuma; todos os documentos estão no nível raiz de `docs/`.
- Documentos analisados: **34 arquivos `.md`**.
- Este relatório é o 35º arquivo da pasta e não participou da comparação.

Métodos utilizados:

1. Inventário completo dos nomes, caminhos e tamanhos.
2. Hash SHA-256 do conteúdo bruto de cada arquivo.
3. Hash SHA-256 do conteúdo normalizado, removendo espaços, tabulações e quebras de linha, para detectar diferenças apenas de formatação.
4. Comparação par a par com `difflib.SequenceMatcher`, similaridade de Jaccard por tokens e sobreposição de sequências de seis palavras.
5. Verificação de frases idênticas após normalização.
6. Leitura manual da finalidade, período, versão e informações exclusivas de cada documento.

Resultado das métricas: os 34 arquivos têm hash bruto e hash normalizado distintos. A maior similaridade textual encontrada foi **22,75%** (`RELATORIO_ETAPA_2.md` × `RELATORIO_ETAPA_3.md`), e não houve frase literal compartilhada entre os pares temáticos analisados. Portanto, não existem cópias exatas; as redundâncias identificadas são de conteúdo e de finalidade.

## 2. Inventário dos arquivos

| # | Arquivo | Bytes | Papel documental |
|---:|---|---:|---|
| 1 | `docs/00_INDICE_E_ORIENTACAO.md` | 2303 | Índice e orientação de leitura |
| 2 | `docs/01_ORIGEM_ENTREGA_1.md` | 1540 | Contexto histórico da Entrega 1 |
| 3 | `docs/02_PLANEJAMENTO_FINAXIS_2_0.md` | 1465 | Planejamento da versão 2.0 |
| 4 | `docs/03_ARQUITETURA_E_ESTRUTURA.md` | 1127 | Arquitetura e tecnologias |
| 5 | `docs/04_MODULOS_FINANCEIROS.md` | 1665 | Visão funcional dos módulos |
| 6 | `docs/05_MIGRACAO_DA_VERSAO_1.md` | 1303 | Migração da versão 1 |
| 7 | `docs/06_AUDITORIA_E_TESTES_INICIAIS.md` | 1080 | Auditoria e evolução inicial dos testes |
| 8 | `docs/07_REVISAO_ENTREGA_4.md` | 1417 | Diagnóstico que originou as correções |
| 9 | `docs/08_ETAPA_1_PREPARACAO.md` | 710 | Resumo da Etapa 1 |
| 10 | `docs/09_ETAPA_2_SEGURANCA.md` | 920 | Resumo da Etapa 2 |
| 11 | `docs/10_ETAPA_3_FINANCEIRO.md` | 936 | Resumo da Etapa 3 |
| 12 | `docs/11_ETAPA_4_INTERFACE.md` | 747 | Resumo da Etapa 4 |
| 13 | `docs/12_ETAPA_5_RELATORIOS.md` | 680 | Resumo da Etapa 5 |
| 14 | `docs/13_ETAPA_6_BACKUPS.md` | 679 | Resumo da Etapa 6 |
| 15 | `docs/14_AJUSTES_TEMA_TABELAS_BOTOES.md` | 1053 | Ajustes de tema, tabelas e botões |
| 16 | `docs/15_AJUSTES_DASHBOARD_GRAFICO.md` | 939 | Ajustes de dashboard e gráfico |
| 17 | `docs/16_INICIALIZADOR_WINDOWS.md` | 772 | Inicializador do Windows |
| 18 | `docs/17_CONTA_DEMONSTRACAO.md` | 852 | Conta de demonstração |
| 19 | `docs/18_REBRANDING_FINAXIS.md` | 718 | Atualização da marca |
| 20 | `docs/19_HOMOLOGACAO_E_PENDENCIAS.md` | 1520 | Homologação e pendências |
| 21 | `docs/FASE_3_AUDITORIA.md` | 2839 | Relatório original da Fase 3 |
| 22 | `docs/FASE_4_RELATORIO.md` | 2824 | Relatório original da Fase 4 |
| 23 | `docs/README.md` | 8974 | Guia geral do projeto |
| 24 | `docs/RELATORIO_AJUSTE_TEMA_ESCURO.md` | 1493 | Relatório original do ajuste de tema |
| 25 | `docs/RELATORIO_ALINHAMENTO_DASHBOARD_CONTA_DEMO.md` | 2816 | Relatório original de dashboard e conta demo |
| 26 | `docs/RELATORIO_CORRECOES_INTERFACE_E_DUPLICIDADE.md` | 2824 | Relatório original de interface e envio duplicado |
| 27 | `docs/RELATORIO_ETAPA_1.md` | 1521 | Relatório original da Etapa 1 |
| 28 | `docs/RELATORIO_ETAPA_2.md` | 2229 | Relatório original da Etapa 2 |
| 29 | `docs/RELATORIO_ETAPA_3.md` | 2976 | Relatório original da Etapa 3 |
| 30 | `docs/RELATORIO_ETAPA_4.md` | 2212 | Relatório original da Etapa 4 |
| 31 | `docs/RELATORIO_ETAPA_5.md` | 2272 | Relatório original da Etapa 5 |
| 32 | `docs/RELATORIO_ETAPA_6.md` | 3253 | Relatório original da Etapa 6 |
| 33 | `docs/RELATORIO_REBRANDING_FINAXIS.md` | 1301 | Relatório original de rebranding |
| 34 | `docs/TEMA_DARK_GOLD.md` | 759 | Especificação do tema Dark + Gold |

## 3. Nomes iguais ou muito semelhantes

Não há dois arquivos com o mesmo nome. Os nomes abaixo são suficientemente parecidos para exigir atenção:

| Documentos | Semelhança |
|---|---|
| `08_ETAPA_1_PREPARACAO.md` × `RELATORIO_ETAPA_1.md` | Mesma etapa e assunto |
| `09_ETAPA_2_SEGURANCA.md` × `RELATORIO_ETAPA_2.md` | Mesma etapa e assunto |
| `10_ETAPA_3_FINANCEIRO.md` × `RELATORIO_ETAPA_3.md` | Mesma etapa e assunto |
| `11_ETAPA_4_INTERFACE.md` × `RELATORIO_ETAPA_4.md` | Mesma etapa e assunto |
| `12_ETAPA_5_RELATORIOS.md` × `RELATORIO_ETAPA_5.md` | Mesma etapa e assunto |
| `13_ETAPA_6_BACKUPS.md` × `RELATORIO_ETAPA_6.md` | Mesma etapa e assunto |
| `14_AJUSTES_TEMA_TABELAS_BOTOES.md` × `RELATORIO_AJUSTE_TEMA_ESCURO.md` | Mesmos ajustes de tema e tabelas |
| `14_AJUSTES_TEMA_TABELAS_BOTOES.md` × `RELATORIO_CORRECOES_INTERFACE_E_DUPLICIDADE.md` | Ajustes de CSS, tema e tabelas |
| `15_AJUSTES_DASHBOARD_GRAFICO.md` × `RELATORIO_ALINHAMENTO_DASHBOARD_CONTA_DEMO.md` | Dashboard, gráfico e conta demo |
| `17_CONTA_DEMONSTRACAO.md` × `18_REBRANDING_FINAXIS.md` × `RELATORIO_REBRANDING_FINAXIS.md` | Conta demo, senha e marca |
| `FASE_3_AUDITORIA.md` × `RELATORIO_ETAPA_3.md` | “Fase 3” e “Etapa 3” são ciclos diferentes; o tema financeiro se sobrepõe |
| `FASE_4_RELATORIO.md` × `RELATORIO_ETAPA_4.md` | “Fase 4” e “Etapa 4” são ciclos diferentes; a interface se sobrepõe |

O uso simultâneo de “Fase” e “Etapa” para ciclos distintos é o principal risco de confusão. Os documentos não devem ser renomeados sem autorização e sem atualização das referências.

## 4. Duplicidade exata

**Quantidade: 0.**

- Não há arquivos com conteúdo integralmente igual.
- Não há arquivos equivalentes após remover espaços, tabulações e quebras de linha.
- Todos os 34 hashes SHA-256 brutos são distintos.
- Todos os 34 hashes SHA-256 normalizados são distintos.
- Nenhum par ultrapassou 22,75% de similaridade textual.

## 5. Duplicidade de conteúdo

Nesta seção estão documentos diferentes que relatam a mesma etapa ou o mesmo conjunto de alterações. Não há cópia literal; há repetição semântica: os arquivos numerados `08` a `13` resumem as mesmas etapas já detalhadas em `RELATORIO_ETAPA_1.md` a `RELATORIO_ETAPA_6.md`.

**Quantidade: 6 pares, envolvendo 12 documentos.**

| Grupo | Documentos | Motivo | Informação exclusiva que impede descarte |
|---|---|---|---|
| Etapa 1 | `docs/08_ETAPA_1_PREPARACAO.md` e `docs/RELATORIO_ETAPA_1.md` | Ambos descrevem preparação, cópia protegida, remoção de `.venv`, manifesto SHA-256, 13 testes e compilação. | O relatório original detalha o manifesto, os bancos privados e as observações sobre o ambiente de teste. |
| Etapa 2 | `docs/09_ETAPA_2_SEGURANCA.md` e `docs/RELATORIO_ETAPA_2.md` | Ambos descrevem bloqueio de login, troca de senha, validação de backup e 16 testes. | O original registra 5 tentativas, 15 minutos, limite de 20 MB e 100.000 registros. |
| Etapa 3 | `docs/10_ETAPA_3_FINANCEIRO.md` e `docs/RELATORIO_ETAPA_3.md` | Ambos descrevem recorrências, moeda BRL/USD/EUR, transferências, parcelamentos e 19 testes. | O original registra limites de 500/5.000 ocorrências e a correção do dia 31. |
| Etapa 4 | `docs/11_ETAPA_4_INTERFACE.md` e `docs/RELATORIO_ETAPA_4.md` | Ambos descrevem temas claro/escuro, `.streamlit/config.toml`, remoção de duplicidades e 19 testes. | O original detalha a paleta, a responsividade e o procedimento de validação visual. |
| Etapa 5 | `docs/12_ETAPA_5_RELATORIOS.md` e `docs/RELATORIO_ETAPA_5.md` | Ambos descrevem filtros, exportações CSV/XLSX/PDF e 20 testes. | O original detalha as três abas do Excel, o PDF em paisagem e o BOM UTF-8. |
| Etapa 6 | `docs/13_ETAPA_6_BACKUPS.md` e `docs/RELATORIO_ETAPA_6.md` | Ambos descrevem checksum, validação, restauração, proteção contra reimportação e 25 testes. | O original registra `integrity_sha256`, fingerprint, `PRAGMA integrity_check` e compatibilidade de schema. |

Conclusão da seção: os pares são redundantes do ponto de vista narrativo, mas não são cópias. Os resumos numerados servem à leitura cronológica; os relatórios originais preservam evidências técnicas, limites e resultados específicos. Nenhum dos dois lados deve ser excluído sem análise e autorização.

## 6. Sobreposição parcial

**Quantidade: 4 grupos, envolvendo 10 documentos.**

| Grupo | Documentos | Conteúdo sobreposto | Conteúdo exclusivo | Severidade |
|---|---|---|---|---|
| Ajustes de tema, tabelas e botões | `docs/14_AJUSTES_TEMA_TABELAS_BOTOES.md`, `docs/RELATORIO_AJUSTE_TEMA_ESCURO.md`, `docs/RELATORIO_CORRECOES_INTERFACE_E_DUPLICIDADE.md` | Contraste, tabelas claras no tema escuro, CSS de botões e campos. | `14` registra o `TypeError` do argumento `theme`; o relatório de tema registra `show_dataframe` e 27 testes; o relatório de correções registra idempotência de lançamentos. | Moderada |
| Dashboard e gráfico | `docs/15_AJUSTES_DASHBOARD_GRAFICO.md`, `docs/RELATORIO_ALINHAMENTO_DASHBOARD_CONTA_DEMO.md` | Alinhamento dos quatro indicadores e substituição dos raios manuais por aro concêntrico no Plotly. | O relatório original também documenta a conta de demonstração, o hash PBKDF2, a coluna `role` e 28 testes. | Moderada |
| Rebranding, conta demo e senha | `docs/17_CONTA_DEMONSTRACAO.md`, `docs/18_REBRANDING_FINAXIS.md`, `docs/RELATORIO_REBRANDING_FINAXIS.md` | Conta `admin@finaxis.demo`, remoção da senha visível, hash PBKDF2 e preservação do identificador interno `Finaxis 2.0`. | `17` foca a conta demo; `18` lista os pontos de atualização da marca; o relatório original reúne os dois temas e a justificativa de segurança. | Alta entre `18` e o relatório; moderada com `17` |
| Testes e homologação | `docs/06_AUDITORIA_E_TESTES_INICIAIS.md`, `docs/19_HOMOLOGACAO_E_PENDENCIAS.md` | Marcos de testes (10, 13, 16, 19, 20, 25 e 28) e ressalva de que os números não devem ser somados. | `06` explica o início da auditoria; `19` consolida a linha do tempo e a lista final de pendências. | Baixa |

Observação: as contagens de testes também aparecem, pontualmente, em `README.md`, `FASE_3_AUDITORIA.md`, `FASE_4_RELATORIO.md` e nos relatórios de etapa. Isso é coerente com cada relatório, mas exige cuidado para não interpretar os números como quantidades cumulativas.

## 7. Assuntos semelhantes que devem ser preservados

Estes documentos tratam de temas próximos, mas têm finalidade, período ou nível de detalhe diferentes. Não foram classificados como duplicidade.

| Documentos | Por que se parecem | Por que devem ser preservados |
|---|---|---|
| `docs/README.md` × `docs/02_PLANEJAMENTO_FINAXIS_2_0.md`, `docs/03_ARQUITETURA_E_ESTRUTURA.md`, `docs/04_MODULOS_FINANCEIROS.md`, `docs/05_MIGRACAO_DA_VERSAO_1.md` | O README apresenta tecnologias, funcionalidades e migração; os documentos numerados aprofundam os mesmos temas. | O README é o guia de uso e instalação; os demais registram planejamento, arquitetura, módulos e migração em nível histórico. |
| `docs/01_ORIGEM_ENTREGA_1.md` × `docs/05_MIGRACAO_DA_VERSAO_1.md` | Ambos citam a base antiga com 11 categorias e nenhum lançamento. | Um descreve a origem do projeto; o outro detalha o processo e a homologação da migração. |
| `docs/07_REVISAO_ENTREGA_4.md` × `docs/FASE_3_AUDITORIA.md`, `docs/FASE_4_RELATORIO.md` | Compartilham observações sobre segurança, interface, relatórios e backups. | `07` é o diagnóstico que orientou as correções; os relatórios de fase registram o que já havia sido implementado e testado. |
| `docs/FASE_3_AUDITORIA.md` × `docs/RELATORIO_ETAPA_3.md` | Nomes parecidos e temas financeiros comuns. | “Fase 3” pertence ao ciclo anterior à Entrega 4; “Etapa 3” pertence ao ciclo posterior de correções. Períodos e escopos diferentes. |
| `docs/FASE_4_RELATORIO.md` × `docs/RELATORIO_ETAPA_4.md` | Nomes parecidos e tema de interface. | “Fase 4” tratou segurança, interface, relatórios e notificações; “Etapa 4” tratou temas claro/escuro e duplicidades da barra lateral. |
| `docs/TEMA_DARK_GOLD.md` × `docs/14_AJUSTES_TEMA_TABELAS_BOTOES.md`, `docs/RELATORIO_AJUSTE_TEMA_ESCURO.md` | Todos tratam do tema escuro. | `TEMA_DARK_GOLD.md` define a identidade visual; os outros registram correções de contraste e compatibilidade. |
| `docs/16_INICIALIZADOR_WINDOWS.md` × `docs/README.md`, `docs/TEMA_DARK_GOLD.md` | Todos explicam como executar o sistema. | `16` documenta a motivação e o funcionamento do BAT; README e tema registram comandos e requisitos. |
| `docs/00_INDICE_E_ORIENTACAO.md` × demais documentos | O índice referencia a coleção inteira. | É um documento de navegação, não um relatório. Precisa ser atualizado, mas não duplicado. |
| `docs/02_PLANEJAMENTO_FINAXIS_2_0.md` × `docs/03_ARQUITETURA_E_ESTRUTURA.md`, `docs/04_MODULOS_FINANCEIROS.md` | Planejamento, arquitetura e módulos descrevem a mesma evolução. | Um define requisitos e decisões; os outros registram a estrutura e as áreas funcionais resultantes. |

## 8. Documentos sem duplicidade relevante

Os 12 documentos abaixo não participam dos grupos de duplicidade ou sobreposição parcial identificados. Alguns têm assunto semelhante a outros, mas função distinta, conforme a seção 7.

1. `docs/00_INDICE_E_ORIENTACAO.md` — índice, embora incompleto.
2. `docs/01_ORIGEM_ENTREGA_1.md` — origem histórica.
3. `docs/02_PLANEJAMENTO_FINAXIS_2_0.md` — planejamento.
4. `docs/03_ARQUITETURA_E_ESTRUTURA.md` — arquitetura.
5. `docs/04_MODULOS_FINANCEIROS.md` — módulos financeiros.
6. `docs/05_MIGRACAO_DA_VERSAO_1.md` — migração.
7. `docs/07_REVISAO_ENTREGA_4.md` — diagnóstico inicial.
8. `docs/16_INICIALIZADOR_WINDOWS.md` — inicializador Windows.
9. `docs/FASE_3_AUDITORIA.md` — relatório original da Fase 3.
10. `docs/FASE_4_RELATORIO.md` — relatório original da Fase 4.
11. `docs/README.md` — guia geral.
12. `docs/TEMA_DARK_GOLD.md` — especificação de tema.

## 9. Resumo quantitativo

| Métrica | Resultado |
|---|---:|
| Documentos analisados | 34 |
| Duplicidades exatas | 0 |
| Pares com duplicidade de conteúdo (mesma etapa) | 6 pares / 12 documentos |
| Grupos de sobreposição parcial | 4 grupos / 10 documentos |
| Total de ocorrências de duplicidade ou sobreposição | 10 ocorrências / 22 documentos |
| Documentos sem duplicidade relevante | 12 |
| Documentos que devem ser preservados | 34 |
| Exclusões recomendadas sem autorização | 0 |

## 10. Problemas e pontos de atenção

1. **Índice incompleto:** `docs/00_INDICE_E_ORIENTACAO.md` lista apenas os documentos `01` a `19`. Ele não menciona `README.md`, `FASE_3_AUDITORIA.md`, `FASE_4_RELATORIO.md`, os `RELATORIO_ETAPA_*`, os relatórios de ajustes, `TEMA_DARK_GOLD.md` nem este relatório de auditoria.
2. **Dupla narrativa das etapas:** as Etapas 1 a 6 aparecem em versão resumida (`08`–`13`) e em relatório original (`RELATORIO_ETAPA_1`–`6`). Isso é útil para consulta, mas aumenta o risco de divergência futura.
3. **Nomenclatura “Fase” × “Etapa”:** `FASE_3_AUDITORIA.md` não é o mesmo documento que `RELATORIO_ETAPA_3.md`; `FASE_4_RELATORIO.md` não é o mesmo que `RELATORIO_ETAPA_4.md`. A semelhança de nomes pode induzir a erro.
4. **Contagens de testes repetidas:** os números aparecem em vários documentos e em marcos diferentes. Não devem ser somados; `06` e `19` já fazem essa ressalva.
5. **README com resumos técnicos:** o README contém seções que resumem a Fase 3, a Fase 4 e a conta de demonstração. Se os relatórios originais mudarem, o README pode ficar desatualizado.
6. **Ausência de links internos:** os documentos praticamente não usam links Markdown entre si. A navegação depende do índice, que está incompleto.
7. **Pasta plana:** 35 arquivos no mesmo nível, sem separação entre guias, relatórios originais e resumos históricos.

## 11. Recomendações de organização

Nenhuma alteração foi executada. As propostas abaixo dependem de autorização.

### Proposta A — conservadora e recomendada

- Manter todos os 34 documentos existentes.
- Atualizar `docs/00_INDICE_E_ORIENTACAO.md` para incluir os 14 documentos legados e este relatório.
- Adicionar ao índice uma coluna de status: “guia”, “resumo histórico”, “relatório original”, “auditoria” e “especificação”.
- Adicionar links “Ver também” entre cada resumo `08`–`13` e seu relatório original correspondente.
- Não excluir, mesclar ou renomear nada.

### Proposta B — consolidação controlada

- Para cada etapa, criar um único documento canônico com duas partes: “Resumo” e “Detalhes técnicos”.
- Mover os documentos substituídos para `docs/arquivo_historico/`, preservando o conteúdo e os nomes.
- Antes de consolidar, revisar as informações exclusivas listadas na seção 5.
- Requer autorização específica e atualização de todas as referências.

### Proposta C — reorganização por tipo

- Criar subpastas como `docs/guias/`, `docs/historico/`, `docs/relatorios_originais/` e `docs/auditorias/`.
- Manter o índice como ponto de entrada.
- Renomear apenas quando houver ganho claro de navegação e após atualizar os links.
- Requer autorização e validação de caminhos.

### Recomendação de prioridade

1. Executar a Proposta A primeiro, por ser de baixo risco e não alterar o conteúdo técnico.
2. Avaliar a Proposta B somente depois de confirmar que nenhuma informação exclusiva será perdida.
3. Avaliar a Proposta C se a pasta continuar crescendo.

## 12. Validação final

- **Arquivos analisados:** 34.
- **Duplicidades exatas:** 0.
- **Duplicidades de conteúdo:** 6 pares, envolvendo 12 documentos.
- **Sobreposições parciais:** 4 grupos, envolvendo 10 documentos.
- **Documentos que devem ser preservados:** todos os 34.
- **Exclusões, fusões ou renomeações realizadas:** nenhuma.
- **Alterações em código, banco de dados ou funcionalidades:** nenhuma.

Arquivos que precisam de atenção prioritária:

1. `docs/00_INDICE_E_ORIENTACAO.md` — índice incompleto.
2. `docs/08_ETAPA_1_PREPARACAO.md` e `docs/RELATORIO_ETAPA_1.md`
3. `docs/09_ETAPA_2_SEGURANCA.md` e `docs/RELATORIO_ETAPA_2.md`
4. `docs/10_ETAPA_3_FINANCEIRO.md` e `docs/RELATORIO_ETAPA_3.md`
5. `docs/11_ETAPA_4_INTERFACE.md` e `docs/RELATORIO_ETAPA_4.md`
6. `docs/12_ETAPA_5_RELATORIOS.md` e `docs/RELATORIO_ETAPA_5.md`
7. `docs/13_ETAPA_6_BACKUPS.md` e `docs/RELATORIO_ETAPA_6.md`
8. `docs/14_AJUSTES_TEMA_TABELAS_BOTOES.md`, `docs/RELATORIO_AJUSTE_TEMA_ESCURO.md` e `docs/RELATORIO_CORRECOES_INTERFACE_E_DUPLICIDADE.md`
9. `docs/15_AJUSTES_DASHBOARD_GRAFICO.md` e `docs/RELATORIO_ALINHAMENTO_DASHBOARD_CONTA_DEMO.md`
10. `docs/17_CONTA_DEMONSTRACAO.md`, `docs/18_REBRANDING_FINAXIS.md` e `docs/RELATORIO_REBRANDING_FINAXIS.md`
11. `docs/FASE_3_AUDITORIA.md` e `docs/RELATORIO_ETAPA_3.md`
12. `docs/FASE_4_RELATORIO.md` e `docs/RELATORIO_ETAPA_4.md`
