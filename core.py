from datetime import datetime, timedelta
from collections import deque, Counter

# --- Exceções Customizadas ---
# Criar nossas próprias exceções ajuda a identificar exatamente onde a regra 
# de negócio falhou, em vez de lidar com um erro genérico do Python.
class CapacidadeExcedidaException(Exception): pass
class ChamadoNaoEncontradoException(Exception): pass

# --- Classes de Domínio ---
class Chamado:
    # Atributo de Classe: Pertence à classe 'Chamado' como um todo e não a um objeto específico.
    # Serve como um contador global para garantir que cada chamado tenha um número único sequencial.
    _gerador_numero = 1

    # Dicionário constante para mapear a string de prioridade para horas. 
    # Isso evita o uso de múltiplos blocos "if/elif".
    SLA_MAP = {'baixa': 72, 'media': 24, 'alta': 8, 'critica': 4}
    
    # State Machine (Máquina de Estados)
    # Define as regras estritas de transição. A chave é o status atual, e a 
    # lista contém os únicos status de destino permitidos.
    TRANSIÇÕES_VALIDAS = {
        'aberto': ['em_atendimento'],
        'em_atendimento': ['aguardando_cliente', 'resolvido'],
        'aguardando_cliente': ['em_atendimento'],
        'resolvido': ['fechado'],
        'fechado': []
    }

    # Método Construtor: Executado automaticamente sempre que fazemos Chamado(...)
    def __init__(self, titulo, descricao, cliente, prioridade):
        # Normaliza a entrada para minúsculo, evitando erros como "ALTA" ou "Alta"
        prioridade = prioridade.lower()
        
        # Validação preventiva de erro (Fail-fast)
        if prioridade not in self.SLA_MAP:
            raise ValueError(f"Prioridade inválida. Opções: {list(self.SLA_MAP.keys())}")
        
        # Atribui o número atual e incrementa o gerador global para o próximo chamado
        self.numero = Chamado._gerador_numero
        Chamado._gerador_numero += 1
        
        # Atributos de Instância: Pertencem especificamente a ESTE chamado
        self.titulo = titulo
        self.descricao = descricao
        self.cliente = cliente
        self.prioridade = prioridade
        self.status = 'aberto'
        self.data_abertura = datetime.now() # Captura o momento exato da criação
        
        # Calcula o limite de tempo (SLA) convertendo o número de horas em um objeto timedelta
        self.sla_horas = timedelta(hours=self.SLA_MAP[prioridade])
        
        self.tecnico = None
        self.historico = [] # Lista vazia que guardará dicionários de log
        
        # O próprio __init__ já registra a primeira ação no histórico
        self.registrar_acao("Abertura do chamado", "Sistema")

    # Dunder Method __str__: Define como o objeto será exibido se usarmos print(chamado)
    def __str__(self):
        return f"[{self.numero}] {self.titulo} - {self.cliente} | Pri: {self.prioridade} | Status: {self.status} | Tempo: {self.tempo_decorrido()}"

    def tempo_decorrido(self):
        # Retorna a diferença matemática de tempo (datetime atual menos datetime da abertura)
        return datetime.now() - self.data_abertura

    def esta_em_atraso(self):
        # Se já foi resolvido ou fechado, o relógio "para", então nunca estará em atraso
        if self.status in ['resolvido', 'fechado']:
            return False
        # Compara dois objetos timedelta para saber se o tempo gasto é maior que o tempo limite
        return self.tempo_decorrido() > self.sla_horas

    def registrar_acao(self, acao, responsavel):
        # Adiciona um dicionário à lista de histórico para mantermos um rastro de auditoria
        self.historico.append({
            "data": datetime.now().isoformat(), # isoformat() converte a data para string segura para JSON
            "acao": acao,
            "responsavel": responsavel
        })

    def alterar_status(self, novo_status, responsavel):
        # Proteção principal: Verifica se o novo_status está na lista de transições permitidas
        # Usa .get() com uma lista vazia como fallback para evitar KeyError
        if novo_status not in self.TRANSIÇÕES_VALIDAS.get(self.status, []):
            raise ValueError(f"Transição inválida de {self.status} para {novo_status}")
        
        self.status = novo_status
        self.registrar_acao(f"Status alterado para {novo_status}", responsavel)

    def to_dict(self):
        # Transforma o objeto complexo (com métodos e propriedades) em um dicionário simples.
        # Isso é essencial porque APIs REST não conseguem enviar objetos Python nativos, apenas JSON.
        return {
            "numero": self.numero,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "cliente": self.cliente,
            "prioridade": self.prioridade,
            "status": self.status,
            "data_abertura": self.data_abertura.isoformat(),
            "sla_horas": self.sla_horas.total_seconds() / 3600, # Converte o limite de volta para horas (número float)
            "tecnico_id": self.tecnico,
            "historico": self.historico,
            "em_atraso": self.esta_em_atraso()
        }

class Tecnico:
    _gerador_id = 1

    def __init__(self, nome, especialidades, capacidade_maxima=5):
        self.id_tecnico = Tecnico._gerador_id
        Tecnico._gerador_id += 1
        
        self.nome = nome
        # Converte a entrada para Set (Conjunto). Sets são muito mais rápidos que listas
        # para verificar se um item existe lá dentro (ex: "tem especialidade X?").
        self.especialidades = set(especialidades) if isinstance(especialidades, list) else set([especialidades])
        self.chamados_ativos = []
        self.capacidade_maxima = capacidade_maxima

    # O decorator @property transforma este método em um atributo dinâmico.
    # Na prática, você acessa como `tecnico.disponivel` em vez de `tecnico.disponivel()`.
    @property
    def disponivel(self):
        return len(self.chamados_ativos) < self.capacidade_maxima

    def __str__(self):
        return f"{self.nome} (Espec: {', '.join(self.especialidades)}) - Ativos: {len(self.chamados_ativos)}/{self.capacidade_maxima} - Disp: {self.disponivel}"

    def atribuir_chamado(self, numero):
        if not self.disponivel:
            raise CapacidadeExcedidaException(f"Técnico {self.nome} atingiu a capacidade máxima.")
        self.chamados_ativos.append(numero)

    def liberar_chamado(self, numero):
        if numero not in self.chamados_ativos:
            raise ValueError(f"Chamado {numero} não está com o técnico {self.nome}.")
        self.chamados_ativos.remove(numero)

    def tem_especialidade(self, categoria):
        # A busca em um Set em Python é O(1), muito eficiente!
        return categoria in self.especialidades

    def to_dict(self):
        return {
            "id_tecnico": self.id_tecnico,
            "nome": self.nome,
            "especialidades": list(self.especialidades), # Sets não são aceitos no JSON, precisamos converter de volta pra lista
            "chamados_ativos": self.chamados_ativos,
            "capacidade_maxima": self.capacidade_maxima,
            "disponivel": self.disponivel
        }

class CentralDeSupporte:
    def __init__(self, empresa):
        self.empresa = empresa
        
        # Usamos dicionários (Hash Tables) para os chamados e técnicos.
        # Isso garante que a busca por um chamado específico (ex: self.chamados[500])
        # ocorra em tempo constante O(1), sem precisar varrer uma lista usando loops.
        self.chamados = {}  
        self.tecnicos = {}
        
        # Deque (Double Ended Queue) é uma estrutura otimizada do Python para filas.
        # Diferente de uma lista comum, remover o primeiro item (popleft) de um deque
        # não exige que o sistema reposicione todos os outros itens na memória.
        self.fila_nao_atribuidos = deque() 

    def abrir_chamado(self, titulo, descricao, cliente, prioridade):
        # Instancia o objeto Chamado
        chamado = Chamado(titulo, descricao, cliente, prioridade)
        
        # Salva no dicionário usando o número do chamado como chave de acesso rápido
        self.chamados[chamado.numero] = chamado
        
        # Coloca o número no final da fila de espera
        self.fila_nao_atribuidos.append(chamado.numero)
        
        return chamado

    def registrar_tecnico(self, nome, especialidades, capacidade_maxima=5):
        tecnico = Tecnico(nome, especialidades, capacidade_maxima)
        self.tecnicos[tecnico.id_tecnico] = tecnico
        return tecnico

    def buscar_chamado(self, numero):
        # Tenta encontrar a chave no dicionário. Se não achar, levanta nossa exceção customizada.
        if numero not in self.chamados:
            raise ChamadoNaoEncontradoException(f"Chamado {numero} inexistente.")
        return self.chamados[numero]

    def atribuir_tecnico(self, numero_chamado, id_tecnico):
        # Recupera os objetos (Chamado e Tecnico) usando seus respectivos IDs (chaves)
        chamado = self.buscar_chamado(numero_chamado)
        
        if id_tecnico not in self.tecnicos:
            raise ValueError("Técnico não encontrado.")
        
        tecnico = self.tecnicos[id_tecnico]
        
        # Registra o chamado dentro da lista de ativos do técnico
        tecnico.atribuir_chamado(numero_chamado)
        
        # Atualiza os dados do chamado para refletir o dono e o novo status
        chamado.tecnico = id_tecnico
        chamado.alterar_status('em_atendimento', f"Técnico ID {id_tecnico}")
