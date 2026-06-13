from flask import Flask, jsonify, request

from helpdesk_caio_marcos_karlos import (
    CapacidadeExcedidaException,
    CentralDeSupporte,
    ChamadoNaoEncontradoException,
    TecnicoNaoEncontradoException,
)


app = Flask(__name__)
central = CentralDeSupporte("Ciesa Solutions")


def resposta_erro(mensagem, codigo=400):
    return jsonify({"erro": mensagem}), codigo


def obter_json():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValueError("JSON invalido no corpo da requisicao.")
    return dados


def parse_bool(valor):
    if valor is None:
        return None
    valor_normalizado = str(valor).strip().lower()
    if valor_normalizado == "true":
        return True
    if valor_normalizado == "false":
        return False
    raise ValueError("Parametro disponivel deve ser true ou false.")


@app.errorhandler(404)
def tratar_404(_erro):
    return resposta_erro("Recurso nao encontrado.", 404)


@app.errorhandler(405)
def tratar_405(_erro):
    return resposta_erro("Metodo nao permitido.", 405)


@app.route("/chamados", methods=["POST"])
def abrir_chamado():
    try:
        dados = obter_json()
        campos_obrigatorios = ["titulo", "descricao", "cliente", "prioridade"]
        faltando = [campo for campo in campos_obrigatorios if campo not in dados]
        if faltando:
            return resposta_erro(f"Campos obrigatorios ausentes: {', '.join(faltando)}", 400)

        chamado = central.abrir_chamado(
            dados["titulo"],
            dados["descricao"],
            dados["cliente"],
            dados["prioridade"],
        )
        return jsonify(chamado.to_dict()), 201
    except ValueError as erro:
        return resposta_erro(str(erro), 400)


@app.route("/chamados", methods=["GET"])
@app.route("/chamados/", methods=["GET"])
def listar_chamados():
    numero = request.args.get("numero", type=int)
    if numero is not None:
        try:
            chamado = central.buscar_chamado(numero)
            return jsonify(chamado.to_dict()), 200
        except ChamadoNaoEncontradoException as erro:
            return resposta_erro(str(erro), 404)

    status = request.args.get("status")
    chamados = central.listar_chamados(status=status)
    return jsonify([chamado.to_dict() for chamado in chamados]), 200


@app.route("/chamados/<int:numero>", methods=["GET"])
def buscar_chamado(numero):
    try:
        chamado = central.buscar_chamado(numero)
        return jsonify(chamado.to_dict()), 200
    except ChamadoNaoEncontradoException as erro:
        return resposta_erro(str(erro), 404)


@app.route("/chamados/<int:numero>/status", methods=["PATCH"])
def alterar_status(numero):
    try:
        dados = obter_json()
        if "novo_status" not in dados or "responsavel" not in dados:
            return resposta_erro("Campos obrigatorios ausentes: novo_status, responsavel", 400)

        chamado = central.buscar_chamado(numero)
        chamado.alterar_status(dados["novo_status"], dados["responsavel"])
        return jsonify(chamado.to_dict()), 200
    except ChamadoNaoEncontradoException as erro:
        return resposta_erro(str(erro), 404)
    except ValueError as erro:
        return resposta_erro(str(erro), 400)


@app.route("/chamados/<int:numero>/resolver", methods=["PATCH"])
def resolver_chamado(numero):
    try:
        dados = obter_json()
        if "id_tecnico" not in dados or "descricao_solucao" not in dados:
            return resposta_erro("Campos obrigatorios ausentes: id_tecnico, descricao_solucao", 400)

        chamado = central.resolver_chamado(numero, dados["id_tecnico"], dados["descricao_solucao"])
        return jsonify(chamado.to_dict()), 200
    except ChamadoNaoEncontradoException as erro:
        return resposta_erro(str(erro), 404)
    except TecnicoNaoEncontradoException as erro:
        return resposta_erro(str(erro), 404)
    except PermissionError as erro:
        return resposta_erro(str(erro), 403)
    except ValueError as erro:
        return resposta_erro(str(erro), 400)
    except CapacidadeExcedidaException as erro:
        return resposta_erro(str(erro), 400)


@app.route("/chamados/em-atraso", methods=["GET"])
def chamados_em_atraso():
    chamados = central.listar_em_atraso()
    return jsonify([chamado.to_dict() for chamado in chamados]), 200


@app.route("/tecnicos", methods=["POST"])
def registrar_tecnico():
    try:
        dados = obter_json()
        campos_obrigatorios = ["nome", "especialidades"]
        faltando = [campo for campo in campos_obrigatorios if campo not in dados]
        if faltando:
            return resposta_erro(f"Campos obrigatorios ausentes: {', '.join(faltando)}", 400)

        tecnico = central.registrar_tecnico(
            dados["nome"],
            dados["especialidades"],
            dados.get("capacidade_maxima", 5),
        )
        return jsonify(tecnico.to_dict()), 201
    except ValueError as erro:
        return resposta_erro(str(erro), 400)


@app.route("/tecnicos", methods=["GET"])
def listar_tecnicos():
    try:
        disponivel = parse_bool(request.args.get("disponivel"))
        tecnicos = central.listar_tecnicos(disponivel=disponivel)
        return jsonify([tecnico.to_dict() for tecnico in tecnicos]), 200
    except ValueError as erro:
        return resposta_erro(str(erro), 400)


@app.route("/tecnicos/ranking", methods=["GET"])
def ranking_tecnicos():
    return jsonify(central.ranking_tecnicos()), 200


@app.route("/atribuicao/automatica", methods=["POST"])
def atribuicao_automatica():
    resultado = central.atribuicao_automatica()
    return jsonify(resultado), 200


@app.route("/painel", methods=["GET"])
def painel_operacional():
    return jsonify(central.painel_operacional()), 200


if __name__ == "__main__":
    app.run(debug=True)
