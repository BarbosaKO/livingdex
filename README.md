# Living Dex Tracker

Um aplicativo web para rastrear sua coleção de Pokémon (Living Dex) com suporte a importação de arquivos .sav de jogos reais e gerenciamento de boxes.

## Funcionalidades

- **Pokédex Completa**: Visualização de todos os Pokémon com sprites, thumbnails e descrições
- **Gerenciamento de Coleção**: Adicione Pokémon manualmente ou importe de saves reais
- **Sistema de Boxes**: 14 boxes com 30 slots cada, com suporte a drag-and-drop
- **Importação de Saves**: Suporte para Geração 3 (GBA) e Geração 4 (NDS)
- **Sons dos Pokémon**: Reprodução automática dos cries ao acessar detalhes
- **Navegação Intuitiva**: Botões próximo/anterior na Pokédex
- **Visualização Detalhada**: Informações completas de cada Pokémon instância

## Requisitos

- Python 3.8 ou superior
- Flask
- SQLAlchemy
- Outras dependências listadas em `requirements.txt`

## Instalação

1. **Clone o repositório**:
   ```bash
   git clone <seu-repositorio>
   cd livingdex
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare o banco de dados**:
   ```bash
   python seed.py
   ```
   Este comando irá:
   - Criar o arquivo `livingdex.db` se não existir
   - Popular o banco com todas as espécies de Pokémon
   - Configurar os boxes padrão
   - Importar dados do `pokedex.json`

4. **Execute a aplicação**:
   ```bash
   python app.py
   ```

5. **Acesse a aplicação**:
   Abra seu navegador em `http://127.0.0.1:5000`

## Estrutura do Projeto

```
livingdex/
├── app.py                    # Aplicação Flask principal
├── models.py                 # Modelos do banco de dados
├── database.py               # Configuração do banco de dados
├── config.py                 # Configurações da aplicação
├── seed.py                   # Script para popular o banco de dados
├── pokedex.json              # Dados da Pokédex (espécies, descrições, imagens)
├── routes/                   # Rotas da aplicação
│   ├── pokemon.py           # Rotas da Pokédex e coleção
│   ├── boxes.py             # Rotas dos boxes
│   ├── saves.py             # Rotas de importação de saves
│   └── dex.py               # Rotas do dashboard
├── parsers/                  # Parsers de arquivos .sav
│   ├── base.py              # Parser base
│   ├── gen3.py              # Parser para Geração 3 (GBA)
│   └── gen4.py              # Parser para Geração 4 (NDS)
├── templates/                # Templates Jinja2
│   ├── base.html            # Template base
│   ├── index.html           # Página inicial
│   ├── pokedex/             # Templates da Pokédex
│   ├── pokemon/             # Templates da coleção
│   ├── boxes/               # Templates dos boxes
│   └── saves/               # Templates de importação
└── static/                   # Arquivos estáticos
    ├── sprites/             # Sprites dos Pokémon
    ├── thumbnails/          # Thumbnails dos Pokémon
    ├── hires/               # Imagens em alta resolução
    ├── cries/               # Sons dos Pokémon (.ogg)
    └── js/                  # JavaScript (drag-and-drop, etc.)
```

## Uso

### Visualizar Pokédex
- Acesse `/pokedex` para ver todos os Pokémon
- Clique em um Pokémon para ver detalhes completos
- Use os botões "Anterior" e "Próximo" para navegar

### Adicionar Pokémon Manualmente
- Acesse `/pokemon/add`
- Preencha o formulário com os dados do Pokémon
- O Pokémon será automaticamente colocado no primeiro slot disponível

### Importar de Arquivo .sav
1. Acesse `/saves`
2. Selecione a geração do jogo
3. Faça upload do arquivo .sav
4. Revise os Pokémon encontrados na tela de staging
5. Selecione os Pokémon que deseja importar
6. Clique em "Importar Selecionados"

### Gerenciar Boxes
- Acesse `/boxes` para ver todos os boxes
- Clique em um box para ver seus 30 slots
- Arraste e solte Pokémon para mover entre slots
- Use o botão "Mover para Box" para transferir entre boxes

### Ver sua Coleção
- Acesse `/pokemon` para ver todos os Pokémon importados
- Use a paginação para navegar entre páginas
- Clique em "Excluir" para remover um Pokémon da coleção

## Formatos de Arquivos

### pokedex.json
O arquivo `pokedex.json` deve conter a estrutura:
```json
{
  "pokemon": [
    {
      "id": 1,
      "name": "Bulbasaur",
      "description": "Descrição do Pokémon",
      "generation_introduced": 1,
      "has_gender_differences": false,
      "image": {
        "sprite": "/static/sprites/001.png",
        "thumbnail": "/static/thumbnails/001.png",
        "hires": "/static/hires/001.png"
      }
    }
  ]
}
```

### Arquivos de Som
Coloque os arquivos de som dos Pokémon em `.ogg` em `static/cries/`:
- `1.ogg` para Bulbasaur
- `2.ogg` para Ivysaur
- E assim por diante...

## Troubleshooting

### Erro "database is locked"
Se encontrar este erro:
1. Feche todos os processos Python em execução
2. Reinicie o servidor com `python app.py`

### Imagens não aparecem
- Verifique se os arquivos de imagem estão em `static/sprites/`, `static/thumbnails/` e `static/hires/`
- Verifique se os caminhos em `pokedex.json` estão corretos

### Som não toca
- Verifique se os arquivos `.ogg` estão em `static/cries/`
- Alguns navegadores bloqueiam autoplay; use o botão manual 🔊

### Parser não funciona
- Verifique se o arquivo .sav é válido
- Confirme que selecionou a geração correta
- O parser Gen 3 suporta Ruby/Sapphire/Emerald/FireRed/LeafGreen

## Desenvolvimento

Para rodar em modo de desenvolvimento:
```bash
python app.py
```

O servidor roda em modo debug com auto-reload.

## Contribuindo

Contribuições são bem-vindas! Sinta-se livre para abrir issues e pull requests.

## Licença

Este projeto é para uso pessoal e educacional.