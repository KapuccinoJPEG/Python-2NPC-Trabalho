# HelpDesk Pro

Sistema interno de gestão de chamados desenvolvido em Python com orientação a objetos e exposto via API REST com Flask.

## Estrutura do Projeto

- `helpdesk_caio_marcos_karlos.py` - Classes de domínio, exceções e demonstração executável.
- pp.py - API Flask com todos os endpoints JSON.
- core.py - Wrapper de compatibilidade para a implementação principal.
- 
equirements.txt - Dependências da aplicação e da API.

---

## 🚀 Instalação e Execução

### 1. Pré-requisitos
- Python 3.8 ou superior instalado.
- Ambiente Virtual (Opcional, mas recomendado).

### 2. Instalar as dependências
Navegue até a pasta do projeto e execute:
``bash
pip install -r requirements.txt
``

### 3. Modos de Execução
**Modo 1: Teste Visual do Domínio (Terminal)**
Testa a lógica das classes sem ligar o servidor.
``bash
python helpdesk_caio_marcos_karlos.py
``

**Modo 2: Rodar o Servidor da API (Flask)**
Inicia a aplicação web para receber requisições HTTP (Postman, REST Client, Insomnia).
``bash
python app.py
``

---

## 🛠️ Decisão de Estrutura de Dados
Os chamados são armazenados internamente em um dicionário, onde a chave é o número do chamado. Isso permite uma busca em tempo constante $O(1)$, proporcionando alto desempenho mesmo com um grande volume de registros.

---

## 📚 Documentação da API

A API foi desenvolvida seguindo o padrão REST. O formato de transferência de dados aceito e devolvido é exclusivamente **JSON**. 

**URL Base Local:** http://127.0.0.1:5000

### 1. 📊 Painel (Dashboard)
Retorna estatísticas operacionais da central (chamados em atendimento, chamados em atraso, técnicos disponíveis e top clientes).

- **GET /painel**
- **Corpo:** *Nenhum*

### 2. 👨‍💻 Técnicos

#### Registrar Técnico
- **POST /tecnicos**
- **Corpo (JSON):**
``json
{
  "nome": "João Carlos",
  "especialidades": ["Hardware", "Redes"],
  "capacidade_maxima": 5
}
``

#### Listar Técnicos
- **GET /tecnicos**
- **Parâmetros Opcionais (URL):** ?disponivel=true ou ?disponivel=false

#### Ranking de Técnicos
- **GET /tecnicos/ranking**
- **Corpo:** *Nenhum* (Retorna técnicos ordenados por número de chamados resolvidos).

### 3. 🎫 Chamados

#### Abrir Chamado
- **POST /chamados**
- **Corpo (JSON):**
``json
{
  "titulo": "Problema no Wi-Fi",
  "descricao": "A internet cai de hora em hora",
  "cliente": "Empresa XPTO",
  "prioridade": "alta"
}
``
*(Prioridades aceitas: baixa, media, alta, critica)*

#### Listar Chamados
- **GET /chamados**
- **Parâmetros Opcionais (URL):** ?status=aberto ou ?numero=1

#### Buscar Chamado por ID
- **GET /chamados/<numero>**
*(Exemplo: /chamados/1)*

#### Listar Chamados em Atraso (Violação de SLA)
- **GET /chamados/em-atraso**

### 4. 🔀 Andamento e Finalização

#### Alterar Status Manualmente
- **PATCH /chamados/<numero>/status**
- **Corpo (JSON):**
``json
{
  "novo_status": "em_analise",
  "responsavel": "Admin_Sistema"
}
``

#### Resolver um Chamado
- **PATCH /chamados/<numero>/resolver**
- **Corpo (JSON):**
``json
{
  "id_tecnico": 1,
  "descricao_solucao": "Cabo de rede foi substituido."
}
``

### 5. 🤖 Sistema Automático

#### Atribuição Dinâmica
- **POST /atribuicao/automatica**
- **Corpo:** *Nenhum*
- **Descrição:** O sistema analisa todos os chamados com status berto e tenta designá-los automaticamente aos técnicos disponíveis, cruzando os dados das especialidades e verificando se não ultrapassam sua capacidade_maxima.
