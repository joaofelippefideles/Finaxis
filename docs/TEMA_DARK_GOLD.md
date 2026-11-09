# Finaxis — Tema Dark + Gold

Esta versão aplica a identidade visual da imagem de referência:
- fundo principal quase preto;
- sidebar grafite/oliva escura;
- item selecionado em tom dourado discreto;
- ícones Material em branco, estilo outline;
- cartões e painéis em tons escuros com bordas suaves;
- gráficos com paleta dourada.

As rotinas de navegação, autenticação, cálculos e banco de dados foram preservadas.
A base SQLite existente foi mantida na pasta `data/`.

## Executar no Windows PowerShell (na raiz do projeto)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Não copie a pasta `.venv` de outro computador. Ela deve ser criada localmente.
