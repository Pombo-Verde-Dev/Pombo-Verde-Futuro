# 🎓 Sala do Futuro API Client

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Async](https://img.shields.io/badge/async-asyncio-green.svg)](https://docs.python.org/3/library/asyncio.html)

**Cliente Python não-oficial para a API da Sala do Futuro (SEDUC-SP)**

*Acesse suas notas, frequência, agenda e muito mais de forma programática*

[Instalação](#-instalação) •
[Quickstart](#-quickstart) •
[Documentação](#-documentação) •
[Exemplos](#-exemplos)

</div>

---

## ✨ Features

<table>
<tr>
<td>

### 📚 Acadêmico
- ✅ Buscar notas e avaliações
- ✅ Consultar frequência/faltas
- ✅ Visualizar agenda diária/semanal
- ✅ Acompanhar calendário escolar

</td>
<td>

### 📱 Comunicação
- ✅ Notificações da SEDUC
- ✅ Avisos do mural escolar
- ✅ Feed unificado de mensagens
- ✅ Marcar como lido

</td>
</tr>
<tr>
<td>

### 🤖 AI-Powered
- ✅ Gerador de redações (Gemini)
- ✅ Análise de desempenho
- ✅ Sugestões personalizadas
- ✅ Resumos automáticos

</td>
<td>

### 🛠️ Dev-Friendly
- ✅ API async (asyncio)
- ✅ Type hints completo
- ✅ Cache inteligente
- ✅ Event system (discord.py style)

</td>
</tr>
</table>

---

## 🚀 Instalação

### Requisitos
- Python 3.10+
- pip ou poetry

### Via Git
```bash
git clone https://github.com/Pombo-Verde-Dev/salafuturo.git
cd salafuturo
pip install -r requirements.txt
```

### Estrutura do Projeto
```
salafuturo/
├── salafuturo/          # Código principal
│   ├── core/            # HTTP, cache, config
│   ├── models/          # User, Room, Aviso, etc.
│   ├── generator/       # AI (Gemini)
│   └── utils/           # Helpers
├── examples/            # Exemplos de uso
├── .env.example         # Template de configuração
└── README.md
```

---

## ⚙️ Configuração

### 1. Copiar arquivo de ambiente
```bash
cp .env.example .env
```

### 2. Preencher credenciais
```env
# Suas credenciais
RA=1234567890123
SENHA=sua_senha_aqui
UF=SP

# Chaves de API (obtenha via DevTools)
SED_SUBSCRIPTION_KEY=sua_chave_aqui
SED_SUBSCRIPTION_KEY2=sua_chave_aqui
SED_SUBSCRIPTION_KEY3=sua_chave_aqui

# Opcional: Gemini AI
GEMINI_API_KEY=sua_chave_gemini
```

### 🔍 Como obter as chaves de API

<details>
<summary>📖 Clique para expandir</summary>

As chaves `SED_SUBSCRIPTION_KEY` são obtidas via análise de tráfego de rede:

1. Acesse o [site oficial da Sala do Futuro](https://saladofuturo.educacao.sp.gov.br/)
2. faça login com seu RA, UF e Senha
3. Abra o DevTools do navegador (F12)
4. Vá para a aba **Network** (Rede)
5. Faça login normalmente
6. Procure requests para `sedintegracoes.educacao.sp.gov.br`
7. Clique em uma requisição e vá em **Headers**
8. Copie o valor de `Ocp-Apim-Subscription-Key`

Repita para as 3 chaves (Estão em endpoint diferentes. Para encontrar vai depender da api usada).

**⚠️ Estas chaves podem mudar periodicamente.**

</details>

---

## 💻 Quickstart

### Exemplo Básico

```python
import asyncio
import os
from dotenv import load_dotenv
import salafuturo as sf

load_dotenv()

async def main():
    # Criar cliente
    async with sf.Client(
        ra=os.environ["RA"],
        uf=os.environ["UF"],
        senha=os.environ["SENHA"],
    ) as client:
        
        # Buscar turmas
        rooms = await client.fetch_rooms()
        print(f"📚 Você tem {len(rooms)} turmas")
        
        for room in rooms:
            print(f"  • {room.name} ({room.curso})")
        
        # Buscar notificações
        notifs = await client.fetch_notifications()
        print(f"\n📩 Você tem {len(notifs)} notificações")
        
        for n in notifs[:5]:
            emoji = "✅" if n.lida else "📩"
            print(f"  {emoji} {n.titulo} - {n.tempo_atras}")

asyncio.run(main())
```

### Saída Esperada
```
📚 Você tem 2 turmas
  • Desenvolvimento de Sistemas - 3ª Série (Técnico)
  • Ensino Médio Regular - 3ª Série (Regular)

📩 Você tem 12 notificações
  📩 BEEM - Últimos dias para inscrição! - 2h atrás
  ✅ Nova websérie disponível - ontem
  📩 Copa da Escola 2024 - 3d atrás
  ✅ Resultado das Olimpíadas - 1sem atrás
  📩 Férias escolares - 2sem atrás
```

---

## 📖 Documentação

### Modelos Principais

#### 📚 User (Usuário)
```python
user = client.user

print(user.name)          # Nome completo
print(user.username)      # UserName criado pela Sed
print(user.email)         # Email institucional

# Métodos disponíveis
await user.fetch_rooms()              # Turmas
await user.fetch_materias()           # Disciplinas
await user.fetch_faltas()             # Faltas
await user.fetch_avaliacoes()         # Notas
await user.fetch_agenda_dia()         # Agenda de hoje
await user.fetch_notifications()      # Notificações
await user.fetch_feed(room_id)        # Feed unificado
```

#### 🏫 Room (Turma)
```python
room = rooms[0]

print(room.name)              # Nome curto
print(room.curso)             # Curso
print(room.turno_nome)        # Manhã/Tarde/Noite
print(room.progresso_ano)     # 0.0 a 1.0

# Métodos
tasks = await room.fetch_tasks()      # Tarefas
essays = await room.fetch_essays()    # Redações
```

#### 📩 Notificacao
```python
notif = notifs[0]

print(notif.titulo)           # Título
print(notif.texto_limpo)      # Conteúdo sem HTML
print(notif.tempo_atras)      # "2h atrás"
print(notif.categoria)        # ESTAGIO, OLIMPIADA, etc.
print(notif.prioridade)       # URGENTE, ALTA, MEDIA, BAIXA

# Marcar como lida
await notif.mark_as_read()
```

#### 📌 Aviso (Mural)
```python
aviso = avisos[0]

print(aviso.titulo)           # Título
print(aviso.autor.nome)       # Quem postou
print(aviso.fixado)           # Se está fixado
print(aviso.visivel)          # Se está visível agora
print(aviso.dias_restantes)   # Dias até expirar

# Marcar como lido
await aviso.mark_as_read(user.id)
```

#### 📊 Falta & ResumoFaltas
```python
faltas = await user.fetch_faltas()
resumo = await user.fetch_resumo_faltas()

# Estatísticas
print(resumo.total_aulas)              # Total de faltas
print(resumo.total_justificadas)       # Faltas justificadas
print(resumo.por_disciplina)           # {"Matemática": 5, ...}
print(resumo.disciplina_mais_faltas)   # Disciplina com mais faltas

# Frequência
freq = resumo.frequencia_percentual(800)  # 800 = total de aulas no ano
print(f"Frequência: {freq}%")
```

#### 📝 Avaliacao & ResumoAvaliacoes
```python
avals = await user.fetch_avaliacoes()
resumo = await user.fetch_resumo_avaliacoes()

# Por disciplina
for disc, avals in resumo.por_disciplina.items():
    print(f"{disc}: {len(avals)} avaliações")

# Médias
medias = resumo.medias_gerais
for disc, media in medias.items():
    print(f"{disc}: {media}")
```

#### 📅 DiaAgenda (Agenda do Dia)
```python
from datetime import date

agenda = await user.fetch_agenda_dia(date.today())

print(f"📅 {agenda.data_formatada} ({agenda.dia_semana})")
print(f"⏰ {agenda.periodo}")  # 07:00 - 12:30
print(f"📚 {agenda.total_aulas} aulas")

# Aula atual
if aula := agenda.aula_atual:
    print(f"🔴 AGORA: {aula.disciplina} ({aula.horario})")

# Próxima aula
if proxima := agenda.proxima_aula:
    print(f"⏭️  PRÓXIMA: {proxima.disciplina} às {proxima.inicio_fmt}")

# Listar todas
for aula in agenda.aulas:
    if aula.is_intervalo:
        print(f"  ☕ Intervalo - {aula.horario}")
    else:
        print(f"  {aula.emoji} {aula.disciplina} - {aula.horario}")
```

---

## 🎨 Exemplos Avançados

### 📊 Dashboard de Desempenho

```python
async def dashboard(client):
    user = client.user
    
    # Buscar dados
    resumo_notas = await user.fetch_resumo_avaliacoes()
    resumo_faltas = await user.fetch_resumo_faltas()
    
    print("=" * 50)
    print("📊 DASHBOARD ACADÊMICO")
    print("=" * 50)
    
    # Médias por disciplina
    print("\n📈 MÉDIAS:")
    for disc, media in resumo_notas.medias_gerais.items():
        emoji = "🟢" if media >= 7 else "🟡" if media >= 5 else "🔴"
        print(f"  {emoji} {disc}: {media}")
    
    # Frequência
    freq = resumo_faltas.frequencia_percentual(800)
    emoji = "🟢" if freq >= 75 else "🟡" if freq >= 60 else "🔴"
    print(f"\n{emoji} FREQUÊNCIA: {freq}%")
    print(f"  Total de faltas: {resumo_faltas.total_aulas}")
    print(f"  Justificadas: {resumo_faltas.total_justificadas}")
```

### 🤖 Gerador de Redações com IA

```python
async def gerar_redacao(client):
    # Buscar redações pendentes
    room = (await client.fetch_rooms())[0]
    essays = await room.fetch_essays()
    
    if not essays:
        print("📝 Nenhuma redação pendente")
        return
    
    essay = essays[0]
    detail = await essay.fetch_detail()
    
    print(f"📝 Gerando redação: {detail.title}")
    print(f"📋 Tema: {detail.statement}")
    print(f"✍️  Gênero: {detail.genre.name}")
    print(f"📏 {detail.genre.min_words}-{detail.genre.max_words} palavras")
    
    # Gerar com IA (requer GEMINI_API_KEY)
    redacao = await essay.generate(temperature=0.7)
    
    print(f"\n{'=' * 60}")
    print(f"📄 {redacao.title}")
    print(f"{'=' * 60}\n")
    print(redacao.text)
    print(f"\n📊 {redacao.word_count} palavras")
    print(f"⏱️  Gerado em {redacao.generation_time:.1f}s")
    
    # Submeter
    await essay.submit(
        title=redacao.title,
        body=redacao.text,
        duration=redacao.generation_time
    )
    print("✅ Redação enviada!")
```

### 📱 Monitor de Notificações

```python
import asyncio

async def monitor_notificacoes(client):
    """Verifica novas notificações a cada 5 minutos."""
    
    notifs_vistas = set()
    
    while True:
        notifs = await client.fetch_notifications()
        
        for n in notifs:
            if n.id not in notifs_vistas and not n.lida:
                # Nova notificação!
                print(f"\n🔔 NOVA: {n.titulo}")
                print(f"   {n.texto_limpo[:100]}...")
                
                if n.prioridade.value == "urgente":
                    print("   ⚠️  URGENTE!")
                
                notifs_vistas.add(n.id)
        
        await asyncio.sleep(300)  # 5 minutos
```

### 📅 Agenda Semanal

```python
async def agenda_semana(client):
    from datetime import date, timedelta
    
    hoje = date.today()
    segunda = hoje - timedelta(days=hoje.weekday())
    
    print("📅 AGENDA DA SEMANA\n")
    
    for i in range(5):  # Segunda a Sexta
        dia_atual = segunda + timedelta(days=i)
        agenda = await client.user.fetch_agenda_dia(dia_atual)
        
        print(f"\n{'=' * 50}")
        print(f"{agenda.dia_semana} - {agenda.data_formatada}")
        print(f"{'=' * 50}")
        
        if agenda.total_aulas == 0:
            print("  🚫 Sem aulas")
            continue
        
        print(f"⏰ {agenda.periodo}")
        print(f"📚 {agenda.total_aulas} aulas\n")
        
        for aula in agenda.aulas:
            if aula.is_intervalo:
                continue
            status = "🔴" if aula.em_andamento else "⏱️"
            print(f"  {status} {aula.emoji} {aula.disciplina}")
            print(f"     {aula.horario}")
```

---

## 🛠️ Desenvolvimento

### Estrutura de Código

```python
salafuturo/
├── core/              # Núcleo do sistema
│   ├── http.py        # Cliente HTTP async
│   ├── cache.py       # Sistema de cache
│   ├── config.py      # Configurações
│   ├── errors.py      # Exceções customizadas
│   ├── enums.py       # Enumerações
│   └── state.py       # Estado da conexão
│
├── models/            # Modelos de dados
│   ├── user.py        # Usuário
│   ├── room.py        # Turma
│   ├── notification.py # Notificação
│   ├── mural.py       # Avisos
│   ├── agenda.py      # Agenda/Aulas
│   ├── falta.py       # Faltas
│   ├── essay.py       # Redações
│   └── ...
│
├── generator/         # IA (Gemini)
│   └── gemini.py
│
└── utils/             # Utilitários
    ├── time.py        # Datas/tempo
    ├── html.py        # Parse HTML
    ├── query.py       # URL encoding
    └── formatters.py  # Formatação
```

### Executar Testes

```bash
# TODO: Adicionar testes
pytest tests/ -v
```

### Code Style

```bash
# Formatar código
black salafuturo/

# Checar tipos
mypy salafuturo/

# Linter
ruff check salafuturo/
```

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! 

### Como contribuir:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature incrível'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Diretrizes:
- ✅ Code style: Black
- ✅ Type hints obrigatórios
- ✅ Docstrings em todos os métodos públicos
- ✅ Testes para novas features

---

## 📜 Licença

Este projeto está sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

---

## ⚠️ Disclaimer

**Este projeto é fornecido "como está", apenas para fins educacionais.**

- ❌ **NÃO é oficial** nem afiliado à SEDUC-SP
- ❌ **NÃO fornecemos** chaves de API ou credenciais
- ⚠️ **Use por sua conta e risco**
- ⚠️ O autor não se responsabiliza por uso indevido

**Termos de Uso:**
- ✅ Automação pessoal de **seus próprios dados**
- ❌ Não venda acesso ou distribua credenciais
- ❌ Não faça scraping massivo ou abuse da API
- ✅ Respeite os termos de uso da SEDUC-SP

---

## 📞 Suporte

- 🐛 **Bug reports:** [Abrir issue](https://github.com/Pombo-Verde-Dev/salafuturo/issues)
- 💡 **Feature requests:** [Discussões](https://github.com/Pombo-Verde-Dev/salafuturo/discussions)

---

## 🌟 Stargazers

Se este projeto te ajudou, deixe uma ⭐!

[![Stargazers](https://reporoster.com/stars/Pombo-Verde-Dev/salafuturo)](https://github.com/Pombo-Verde-Dev/salafuturo/stargazers)

---

## 📈 Roadmap

- [x] ✅ Sistema de autenticação
- [x] ✅ Buscar notas e faltas
- [x] ✅ Agenda e calendário
- [x] ✅ Notificações e avisos
- [x] ✅ Gerador de redações IA
- [ ] 🚧 Webhooks para notificações
- [ ] 🚧 CLI interativo
- [ ] 🚧 GUI desktop (PyQt/Tkinter)
- [ ] 🚧 Bot do Discord/Telegram
- [ ] 🚧 Análise preditiva de desempenho

---

<div align="center">

**Feito com ❤️ por estudantes, para estudantes**

⭐ [Star no GitHub](https://github.com/Pombo-Verde-Dev/salafuturo) • 
🐦 [Seguir no Twitter](https://twitter.com/seu-user) • 
💬 [Comunidade Discord](https://discord.gg/seu-server)

</div>
