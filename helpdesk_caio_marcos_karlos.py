from collections import Counter, deque
from datetime import datetime, timedelta


class CapacidadeExcedidaException(Exception):
    pass


class ChamadoNaoEncontradoException(Exception):
    pass


class TecnicoNaoEncontradoException(Exception):
    pass


class Chamado:
    _gerador_numero = 1

    SLA_MAP = {
        "baixa": 72,
        "media": 24,
        "alta": 8,
        "critica": 4,
    }

    TRANSICOES_VALIDAS = {
        "aberto": ["em_atendimento"],
        "em_atendimento": ["aguardando_cliente", "resolvido"],
        "aguardando_cliente": ["em_atendimento"],
        "resolvido": ["fechado"],
        "fechado": [],
    }

    def __init__(self, titulo, descricao, cliente, prioridade):
        prioridade_normalizada = str(prioridade).strip().lower()
        if prioridade_normalizada not in self.SLA_MAP:
            raise ValueError("Prioridade invalida. Use: baixa, media, alta ou critica.")

        self.numero = Chamado._gerador_numero
        Chamado._gerador_numero += 1

        self.titulo = titulo
        self.descricao = descricao
        self.cliente = cliente
        self.prioridade = prioridade_normalizada
        self.status = "aberto"
        self.data_abertura = datetime.now()
        self.sla_horas = timedelta(hours=self.SLA_MAP[prioridade_normalizada])
        self.tecnico = None
        self.historico = []
        self.registrar_acao("Abertura do chamado", "Sistema")

    def __str__(self):
        return (
            f"[{self.numero}] {self.titulo} - {self.cliente} | "
            f"prioridade: {self.prioridade} | status: {self.status} | "
            f"tempo decorrido: {self._formatar_timedelta(self.tempo_decorrido())}"
        )

    def tempo_decorrido(self):
        return datetime.now() - self.data_abertura

    def esta_em_atraso(self):
        if self.status in ["resolvido", "fechado"]:
            return False
        return self.tempo_decorrido() > self.sla_horas

    def registrar_acao(self, acao, responsavel):
        self.historico.append(
            {
                "data": datetime.now().isoformat(),
                "acao": acao,
                "responsavel": responsavel,
            }
        )

    def alterar_status(self, novo_status, responsavel):
        status_normalizado = str(novo_status).strip().lower()
        if status_normalizado not in self.TRANSICOES_VALIDAS.get(self.status, []):
            raise ValueError(f"Transicao invalida de {self.status} para {status_normalizado}")

        self.status = status_normalizado
        self.registrar_acao(f"Status alterado para {status_normalizado}", responsavel)

    def to_dict(self):
        return {
            "numero": self.numero,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "cliente": self.cliente,
            "prioridade": self.prioridade,
            "status": self.status,
            "data_abertura": self.data_abertura.isoformat(),
            "sla_horas": int(self.sla_horas.total_seconds() // 3600),
            "tecnico": self.tecnico,
            "historico": list(self.historico),
            "tempo_decorrido": self._formatar_timedelta(self.tempo_decorrido()),
            "em_atraso": self.esta_em_atraso(),
        }

    @staticmethod
    def _formatar_timedelta(valor):
        total_segundos = int(valor.total_seconds())
        dias, resto = divmod(total_segundos, 86400)
        horas, resto = divmod(resto, 3600)
        minutos, segundos = divmod(resto, 60)
        partes = []
        if dias:
            partes.append(f"{dias}d")
        if horas or partes:
            partes.append(f"{horas}h")
        partes.append(f"{minutos}m")
        partes.append(f"{segundos}s")
        return " ".join(partes)


class Tecnico:
    _gerador_id = 1

    def __init__(self, nome, especialidades, capacidade_maxima=5):
        self.id_tecnico = Tecnico._gerador_id
        Tecnico._gerador_id += 1

        self.nome = nome
        if isinstance(especialidades, (list, tuple, set)):
            self.especialidades = {str(item).strip().lower() for item in especialidades if str(item).strip()}
        else:
            self.especialidades = {str(especialidades).strip().lower()}
        self.chamados_ativos = []
        self.chamados_resolvidos = []
        self.capacidade_maxima = int(capacidade_maxima)

    @property
    def disponivel(self):
        return len(self.chamados_ativos) < self.capacidade_maxima

    def __str__(self):
        especialidades = ", ".join(sorted(self.especialidades)) or "sem especialidades"
        return (
            f"{self.nome} | especialidades: {especialidades} | "
            f"ativos: {len(self.chamados_ativos)}/{self.capacidade_maxima} | disponivel: {self.disponivel}"
        )

    def atribuir_chamado(self, numero):
        if numero in self.chamados_ativos:
            return
        if not self.disponivel:
            raise CapacidadeExcedidaException(f"Tecnico {self.nome} atingiu a capacidade maxima.")
        self.chamados_ativos.append(numero)

    def liberar_chamado(self, numero):
        if numero not in self.chamados_ativos:
            raise ValueError(f"Chamado {numero} nao esta com o tecnico {self.nome}.")
        self.chamados_ativos.remove(numero)

    def tem_especialidade(self, categoria):
        return str(categoria).strip().lower() in self.especialidades

    def registrar_chamado_resolvido(self, numero):
        if numero not in self.chamados_resolvidos:
            self.chamados_resolvidos.append(numero)

    def desempenho(self):
        total_ativos = len(self.chamados_ativos)
        total_resolvidos = len(self.chamados_resolvidos)
        total_trabalhado = total_ativos + total_resolvidos
        taxa_resolucao = 0.0
        if total_trabalhado > 0:
            taxa_resolucao = (total_resolvidos / total_trabalhado) * 100

        return {
            "id_tecnico": self.id_tecnico,
            "nome": self.nome,
            "total_ativos": total_ativos,
            "total_resolvidos": total_resolvidos,
            "taxa_resolucao": round(taxa_resolucao, 2),
        }

    def to_dict(self):
        return {
            "id_tecnico": self.id_tecnico,
            "nome": self.nome,
            "especialidades": sorted(self.especialidades),
            "chamados_ativos": list(self.chamados_ativos),
            "chamados_resolvidos": list(self.chamados_resolvidos),
            "capacidade_maxima": self.capacidade_maxima,
            "disponivel": self.disponivel,
        }


class CentralDeSupporte:
    def __init__(self, empresa):
        self.empresa = empresa
        self.chamados = {}
        self.tecnicos = {}
        self.fila_nao_atribuidos = deque()

    def abrir_chamado(self, titulo, descricao, cliente, prioridade):
        chamado = Chamado(titulo, descricao, cliente, prioridade)
        self.chamados[chamado.numero] = chamado
        self.fila_nao_atribuidos.append(chamado.numero)
        return chamado

    def registrar_tecnico(self, nome, especialidades, capacidade_maxima=5):
        tecnico = Tecnico(nome, especialidades, capacidade_maxima)
        self.tecnicos[tecnico.id_tecnico] = tecnico
        return tecnico

    def buscar_chamado(self, numero):
        numero = int(numero)
        if numero not in self.chamados:
            raise ChamadoNaoEncontradoException(f"Chamado {numero} inexistente.")
        return self.chamados[numero]

    def buscar_tecnico(self, id_tecnico):
        id_tecnico = int(id_tecnico)
        if id_tecnico not in self.tecnicos:
            raise TecnicoNaoEncontradoException(f"Tecnico {id_tecnico} inexistente.")
        return self.tecnicos[id_tecnico]

    def listar_chamados(self, status=None):
        chamados = list(self.chamados.values())
        if status:
            status_normalizado = str(status).strip().lower()
            chamados = [chamado for chamado in chamados if chamado.status == status_normalizado]
        return sorted(chamados, key=lambda chamado: chamado.numero)

    def listar_tecnicos(self, disponivel=None):
        tecnicos = list(self.tecnicos.values())
        if disponivel is not None:
            tecnicos = [tecnico for tecnico in tecnicos if tecnico.disponivel is disponivel]
        return sorted(tecnicos, key=lambda tecnico: tecnico.id_tecnico)

    def atribuir_tecnico(self, numero_chamado, id_tecnico):
        chamado = self.buscar_chamado(numero_chamado)
        tecnico = self.buscar_tecnico(id_tecnico)

        if chamado.status in ["resolvido", "fechado"]:
            raise ValueError("Nao e possivel atribuir tecnico a chamado resolvido ou fechado.")

        if chamado.tecnico == tecnico.id_tecnico:
            return chamado

        if chamado.tecnico is not None:
            tecnico_anterior = self.tecnicos.get(chamado.tecnico)
            if tecnico_anterior and chamado.numero in tecnico_anterior.chamados_ativos:
                tecnico_anterior.liberar_chamado(chamado.numero)

        tecnico.atribuir_chamado(chamado.numero)
        chamado.tecnico = tecnico.id_tecnico

        if chamado.numero in self.fila_nao_atribuidos:
            self.fila_nao_atribuidos.remove(chamado.numero)

        if chamado.status == "aberto":
            chamado.alterar_status("em_atendimento", f"Tecnico {tecnico.nome}")
        elif chamado.status == "aguardando_cliente":
            chamado.alterar_status("em_atendimento", f"Tecnico {tecnico.nome}")

        chamado.registrar_acao(
            f"Chamado atribuido ao tecnico {tecnico.nome}",
            f"Tecnico ID {tecnico.id_tecnico}",
        )
        return chamado

    def _selecionar_tecnico_menos_carregado(self):
        tecnicos_disponiveis = [tecnico for tecnico in self.tecnicos.values() if tecnico.disponivel]
        if not tecnicos_disponiveis:
            return None
        return min(tecnicos_disponiveis, key=lambda tecnico: (len(tecnico.chamados_ativos), tecnico.id_tecnico))

    def atribuicao_automatica(self):
        atribuicoes = []
        fila_atual = list(self.fila_nao_atribuidos)

        for numero_chamado in fila_atual:
            tecnico = self._selecionar_tecnico_menos_carregado()
            if tecnico is None:
                break
            chamado = self.atribuir_tecnico(numero_chamado, tecnico.id_tecnico)
            atribuicoes.append(chamado.to_dict())

        return {
            "quantidade": len(atribuicoes),
            "chamados_atribuidos": atribuicoes,
        }

    def resolver_chamado(self, numero, id_tecnico, descricao_solucao):
        chamado = self.buscar_chamado(numero)
        tecnico = self.buscar_tecnico(id_tecnico)

        if chamado.tecnico != tecnico.id_tecnico:
            raise PermissionError("Somente o tecnico responsavel pode resolver o chamado.")

        chamado.alterar_status("resolvido", tecnico.nome)
        chamado.registrar_acao(f"Solucao registrada: {descricao_solucao}", tecnico.nome)
        tecnico.liberar_chamado(chamado.numero)
        tecnico.registrar_chamado_resolvido(chamado.numero)
        chamado.tecnico = None

        return chamado

    def ranking_tecnicos(self):
        ranking = [tecnico.desempenho() for tecnico in self.tecnicos.values()]
        return sorted(
            ranking,
            key=lambda item: (item["taxa_resolucao"], item["total_resolvidos"]),
            reverse=True,
        )

    def fechar_chamado(self, numero):
        chamado = self.buscar_chamado(numero)
        if chamado.status != "resolvido":
            raise ValueError("Somente chamados resolvidos podem ser fechados.")
        chamado.alterar_status("fechado", "Sistema")
        return chamado

    def listar_em_atraso(self):
        chamados_atrasados = [chamado for chamado in self.chamados.values() if chamado.esta_em_atraso()]
        return sorted(
            chamados_atrasados,
            key=lambda chamado: (chamado.tempo_decorrido() - chamado.sla_horas),
            reverse=True,
        )

    def relatorio_por_prioridade(self):
        relatorio = {prioridade: [] for prioridade in Chamado.SLA_MAP}
        for chamado in self.chamados.values():
            if chamado.status not in ["resolvido", "fechado"]:
                relatorio[chamado.prioridade].append(chamado.to_dict())
        for prioridade in relatorio:
            relatorio[prioridade] = sorted(relatorio[prioridade], key=lambda item: item["numero"])
        return relatorio

    def painel_operacional(self):
        status_contagem = Counter(chamado.status for chamado in self.chamados.values())
        clientes_contagem = Counter(chamado.cliente for chamado in self.chamados.values())

        return {
            "empresa": self.empresa,
            "total_chamados": len(self.chamados),
            "chamados_por_status": dict(status_contagem),
            "em_atraso": [chamado.to_dict() for chamado in self.listar_em_atraso()],
            "tecnicos_disponiveis": [tecnico.to_dict() for tecnico in self.listar_tecnicos(disponivel=True)],
            "top_3_clientes": [
                {"cliente": cliente, "total_chamados": total}
                for cliente, total in clientes_contagem.most_common(3)
            ],
        }

    def to_dict(self):
        return {
            "empresa": self.empresa,
            "chamados": [chamado.to_dict() for chamado in self.listar_chamados()],
            "tecnicos": [tecnico.to_dict() for tecnico in self.listar_tecnicos()],
            "fila_nao_atribuidos": list(self.fila_nao_atribuidos),
            "painel_operacional": self.painel_operacional(),
        }


def demonstracao():
    import json

    central = CentralDeSupporte("Ciesa Solutions")

    central.registrar_tecnico("Ana Costa", ["infraestrutura", "redes"], 4)
    central.registrar_tecnico("Bruno Lima", ["hardware", "suporte"], 3)
    central.registrar_tecnico("Carla Souza", ["sistemas", "banco de dados"], 4)
    central.registrar_tecnico("Diego Alves", ["seguranca", "suporte"], 5)

    chamados = [
        central.abrir_chamado("Sem acesso ao ERP", "Usuario nao consegue entrar no sistema", "Alfa S.A.", "critica"),
        central.abrir_chamado("Troca de monitor", "Monitor com listras na tela", "Beta Ltda.", "baixa"),
        central.abrir_chamado("Email sem envio", "Caixa postal nao envia mensagens", "Gamma Corp.", "alta"),
        central.abrir_chamado("VPN instavel", "Conexao cai varias vezes por dia", "Alfa S.A.", "media"),
        central.abrir_chamado("Backup falhou", "Rotina noturna apresentou erro", "Delta Ind.", "critica"),
        central.abrir_chamado("Impressora offline", "Fila de impressao parada", "Omega Comercio", "baixa"),
        central.abrir_chamado("Senha expirada", "Usuario precisa redefinir senha", "Beta Ltda.", "media"),
        central.abrir_chamado("Sistema lento", "Aplicacao com resposta lenta", "Sigma Tech", "alta"),
    ]

    chamados[-1].data_abertura -= timedelta(hours=80)

    resultado_atribuicao = central.atribuicao_automatica()
    print("Atribuicao automatica:")
    print(json.dumps(resultado_atribuicao, ensure_ascii=False, indent=2))

    chamado_resolvido_1 = central.resolver_chamado(chamados[0].numero, chamados[0].tecnico, "Acesso restabelecido")
    central.resolver_chamado(chamados[1].numero, chamados[1].tecnico, "Monitor substituido")

    central.fechar_chamado(chamado_resolvido_1.numero)

    try:
        chamados[2].alterar_status("fechado", "Gestor")
    except ValueError as erro:
        print(f"Transicao invalida tratada com sucesso: {erro}")

    print("Chamados em atraso:")
    print(json.dumps([chamado.to_dict() for chamado in central.listar_em_atraso()], ensure_ascii=False, indent=2))

    print("Painel operacional:")
    print(json.dumps(central.painel_operacional(), ensure_ascii=False, indent=2))

    print("Ranking de tecnicos:")
    print(json.dumps(central.ranking_tecnicos(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demonstracao()
