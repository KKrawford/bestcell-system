import re
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from collections import Counter

from config import PLATFORM_TOOLS, LAUDOS_DIR


# ======================================================
# CONFIGURAÇÕES ADB
# ======================================================

ADB_TIMEOUT_CURTO = 15
ADB_TIMEOUT_MEDIO = 45
ADB_TIMEOUT_LONGO = 90

DIAGNOSTICO_LAUDOS_DIR = LAUDOS_DIR / "diagnostico"
SOFTWARE_LAUDOS_DIR = DIAGNOSTICO_LAUDOS_DIR / "software"
HARDWARE_LAUDOS_DIR = DIAGNOSTICO_LAUDOS_DIR / "hardware"

SOFTWARE_LAUDOS_DIR.mkdir(parents=True, exist_ok=True)
HARDWARE_LAUDOS_DIR.mkdir(parents=True, exist_ok=True)


DICIONARIO_AMEACAS = {
    "com.samsung.vvm": {
        "nome": "Correio de Voz Samsung",
        "status": "Seguro",
        "detalhe": "Aplicativo nativo do sistema."
    },
    "com.google.android.apps.adm": {
        "nome": "Encontre Meu Dispositivo",
        "status": "Seguro",
        "detalhe": "Ferramenta oficial da Google."
    },
    "com.android.settings": {
        "nome": "Configurações do Android",
        "status": "Seguro",
        "detalhe": "Menu nativo do sistema."
    },

    # Ameaças conhecidas / pacotes suspeitos
    "com.android.setting": {
        "nome": "Falso Menu Configurações",
        "status": "Ameaça Crítica",
        "detalhe": "Spyware camuflado tentando se passar pelo menu real do Android."
    },
    "com.google.system.update": {
        "nome": "Falsa Atualização Google",
        "status": "Ameaça Crítica",
        "detalhe": "Possível trojan bancário ou app malicioso disfarçado de atualização."
    },
    "org.cservices.vservice": {
        "nome": "Cerberus / Spyware",
        "status": "Ameaça Crítica",
        "detalhe": "Aplicativo associado a monitoramento remoto e espionagem comercial."
    },
    "com.system.support": {
        "nome": "Suporte do Sistema Falso",
        "status": "Ameaça Crítica",
        "detalhe": "Possível ferramenta de acesso remoto disfarçada de suporte do sistema."
    },
}


PALAVRAS_SUSPEITAS = [
    "cleaner",
    "booster",
    "battery",
    "saver",
    "flashlight",
    "keylogger",
    "spy",
    "track",
    "tracker",
    "gift",
    "reward",
    "vpn",
    "proxy",
    "remote",
    "admin",
    "support",
]


PERMISSOES_CRITICAS = [
    "READ_SMS",
    "RECEIVE_SMS",
    "SEND_SMS",
    "READ_CONTACTS",
    "RECORD_AUDIO",
    "CAMERA",
    "ACCESS_FINE_LOCATION",
    "ACCESS_COARSE_LOCATION",
    "ACCESS_BACKGROUND_LOCATION",
    "SYSTEM_ALERT_WINDOW",
    "BIND_ACCESSIBILITY_SERVICE",
    "REQUEST_INSTALL_PACKAGES",
    "QUERY_ALL_PACKAGES",
]


# ======================================================
# HELPERS GERAIS
# ======================================================

def agora_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def limpar_nome_arquivo(valor: str):
    valor = (valor or "sem_nome").strip()
    valor = re.sub(r"[^\w\s-]", "", valor, flags=re.UNICODE)
    valor = re.sub(r"\s+", "_", valor)
    return valor[:80] or "sem_nome"


def get_adb_path():
    adb_exe = Path(PLATFORM_TOOLS) / "adb.exe"

    if adb_exe.exists():
        return str(adb_exe)

    return "adb"


def executar_comando(args: list[str], timeout: int = ADB_TIMEOUT_MEDIO):
    try:
        resultado = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )

        return {
            "ok": resultado.returncode == 0,
            "stdout": resultado.stdout or "",
            "stderr": resultado.stderr or "",
            "returncode": resultado.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Tempo limite excedido ao executar: {' '.join(args)}",
            "returncode": -1,
        }

    except Exception as e:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
        }


def adb(args: list[str], timeout: int = ADB_TIMEOUT_MEDIO):
    return executar_comando([get_adb_path()] + args, timeout=timeout)


def adb_shell(args: list[str], timeout: int = ADB_TIMEOUT_MEDIO):
    return adb(["shell"] + args, timeout=timeout)


# ======================================================
# STATUS DO DISPOSITIVO
# ======================================================

def verificar_dispositivo_adb():
    resultado = adb(["devices"], timeout=ADB_TIMEOUT_CURTO)

    if not resultado["ok"]:
        return {
            "ok": False,
            "status": "adb_erro",
            "mensagem": "Não foi possível executar o ADB. Verifique se o platform-tools está instalado corretamente.",
            "detalhe": resultado["stderr"],
            "devices": [],
        }

    linhas = resultado["stdout"].splitlines()
    devices = []

    for linha in linhas[1:]:
        linha = linha.strip()

        if not linha:
            continue

        partes = linha.split()

        if len(partes) >= 2:
            devices.append({
                "serial": partes[0],
                "status": partes[1],
            })

    if not devices:
        return {
            "ok": False,
            "status": "nenhum_dispositivo",
            "mensagem": "Nenhum aparelho foi encontrado. Conecte o celular via USB e ative a depuração USB.",
            "detalhe": resultado["stdout"],
            "devices": [],
        }

    autorizados = [d for d in devices if d["status"] == "device"]
    nao_autorizados = [d for d in devices if d["status"] == "unauthorized"]
    offline = [d for d in devices if d["status"] == "offline"]

    if nao_autorizados:
        return {
            "ok": False,
            "status": "nao_autorizado",
            "mensagem": "O aparelho foi encontrado, mas ainda não autorizou a depuração USB.",
            "detalhe": "Aceite a permissão RSA na tela do celular e tente novamente.",
            "devices": devices,
        }

    if offline:
        return {
            "ok": False,
            "status": "offline",
            "mensagem": "O aparelho aparece como offline no ADB.",
            "detalhe": "Reconecte o cabo USB, altere o modo USB ou reinicie a depuração USB.",
            "devices": devices,
        }

    if len(autorizados) > 1:
        return {
            "ok": False,
            "status": "multiplos_dispositivos",
            "mensagem": "Há mais de um aparelho conectado.",
            "detalhe": "Mantenha apenas um celular conectado para evitar laudo do aparelho errado.",
            "devices": devices,
        }

    return {
        "ok": True,
        "status": "conectado",
        "mensagem": "Aparelho conectado e autorizado.",
        "detalhe": "",
        "devices": devices,
    }

def coletar_identificacao_aparelho_adb():
    """
    Coleta propriedades de identificação diretamente do Android.

    Não consulta banco e não decide o nome comercial definitivo.
    Retorna os dados técnicos para o orquestrador resolver.
    """

    propriedades = {
        "fabricante": "ro.product.manufacturer",
        "marca": "ro.product.brand",
        "modelo": "ro.product.model",
        "modelo_produto": "ro.product.product.model",
        "nome_comercial": "ro.product.marketname",
        "nome_marketing": "ro.config.marketing_name",
        "nome_vendor": "ro.product.vendor.marketname",
        "nome_produto": "ro.product.name",
        "dispositivo": "ro.product.device",
        "versao_android": "ro.build.version.release",
        "nivel_sdk": "ro.build.version.sdk",
        "build": "ro.build.display.id",
        "placa": "ro.product.board",
        "hardware": "ro.hardware",
        "arquitetura": "ro.product.cpu.abi",
    }

    valores = {}

    for chave_amigavel, chave_adb in propriedades.items():
        resultado = adb_shell(
            ["getprop", chave_adb],
            timeout=ADB_TIMEOUT_CURTO
        )

        if not resultado["ok"]:
            continue

        valor = resultado["stdout"].strip()

        if valor:
            valores[chave_amigavel] = valor

    fabricante = (
        valores.get("fabricante")
        or valores.get("marca")
        or "Não identificado"
    )

    modelo_tecnico = (
        valores.get("modelo")
        or valores.get("modelo_produto")
        or valores.get("nome_produto")
        or valores.get("dispositivo")
        or "Não identificado"
    )

    nome_comercial_adb = (
        valores.get("nome_comercial")
        or valores.get("nome_marketing")
        or valores.get("nome_vendor")
        or ""
    )

    fabricante = fabricante.strip()

    if fabricante:
        fabricante = fabricante[0].upper() + fabricante[1:]

    return {
        "fabricante": fabricante,
        "marca": valores.get("marca", ""),
        "modelo_tecnico": modelo_tecnico.strip(),
        "nome_comercial_adb": nome_comercial_adb.strip(),
        "nome_produto": valores.get("nome_produto", ""),
        "dispositivo": valores.get("dispositivo", ""),
        "versao_android": valores.get("versao_android", ""),
        "nivel_sdk": valores.get("nivel_sdk", ""),
        "build": valores.get("build", ""),
        "placa": valores.get("placa", ""),
        "hardware": valores.get("hardware", ""),
        "arquitetura": valores.get("arquitetura", ""),
        "propriedades": valores,
    }


def montar_nome_aparelho(
    identificacao: dict,
    modelo_comercial: str = ""
):
    """
    Monta o nome que será exibido e salvo no diagnóstico.

    Exemplo:
    Samsung Galaxy S24 FE (SM-S721B)
    """

    fabricante = (identificacao.get("fabricante") or "").strip()
    modelo_tecnico = (
        identificacao.get("modelo_tecnico")
        or "Não identificado"
    ).strip()

    nome_comercial = (
        modelo_comercial
        or identificacao.get("nome_comercial_adb")
        or ""
    ).strip()

    if nome_comercial:
        nome_final = nome_comercial

        if (
            fabricante
            and fabricante != "Não identificado"
            and fabricante.casefold() not in nome_final.casefold()
        ):
            nome_final = f"{fabricante} {nome_final}"

        if (
            modelo_tecnico
            and modelo_tecnico != "Não identificado"
            and modelo_tecnico.casefold() not in nome_final.casefold()
        ):
            nome_final = f"{nome_final} ({modelo_tecnico})"

        return nome_final

    if modelo_tecnico != "Não identificado":
        if fabricante and fabricante != "Não identificado":
            if fabricante.casefold() not in modelo_tecnico.casefold():
                return f"{fabricante} {modelo_tecnico}"

        return modelo_tecnico

    return "Aparelho não identificado"


def identificar_aparelho_adb():
    """
    Compatibilidade com chamadas anteriores.

    Retorna uma identificação legível, mas ainda sem consultar
    o cadastro de modelos comerciais.
    """

    identificacao = coletar_identificacao_aparelho_adb()
    return montar_nome_aparelho(identificacao)

# ======================================================
# COLETA DE LAUDOS
# ======================================================

def montar_cabecalho_laudo(titulo: str, cliente: str, aparelho: str):
    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    return [
        "=======================================================",
        f"          {titulo}",
        "=======================================================",
        f" CLIENTE: {cliente}",
        f" APARELHO: {aparelho}",
        f" DATA: {data}",
        "",
    ]


def adicionar_secao(linhas: list[str], titulo: str, conteudo: str):
    linhas.extend([
        "=======================================================",
        titulo,
        "=======================================================",
    ])

    if conteudo.strip():
        linhas.extend(conteudo.splitlines())
    else:
        linhas.append("Nenhuma informação retornada pelo ADB.")

    linhas.append("")

def extrair_secao_laudo(
    raw_text: str,
    titulo_inicio: str,
    titulo_fim: str | None = None
):
    inicio = raw_text.find(titulo_inicio)

    if inicio == -1:
        return ""

    if not titulo_fim:
        return raw_text[inicio:]

    fim = raw_text.find(titulo_fim, inicio)

    if fim == -1:
        return raw_text[inicio:]

    return raw_text[inicio:fim]

def salvar_laudo(tipo: str, cliente: str, linhas: list[str]):
    cliente_limpo = limpar_nome_arquivo(cliente)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if tipo == "software":
        path = SOFTWARE_LAUDOS_DIR / f"Laudo_Software_{cliente_limpo}_{timestamp}.txt"
    else:
        path = HARDWARE_LAUDOS_DIR / f"Laudo_Hardware_{cliente_limpo}_{timestamp}.txt"

    path.write_text("\n".join(linhas), encoding="utf-8")
    return str(path)


def coletar_laudo_software(cliente: str, aparelho: str):
    linhas = montar_cabecalho_laudo(
        "LAUDO TECNICO DE SEGURANCA DO CELULAR",
        cliente,
        aparelho
    )

    comandos = [
        (
            "1. APLICATIVOS DE TERCEIROS INSTALADOS",
            ["pm", "list", "packages", "-3"],
            ADB_TIMEOUT_MEDIO
        ),
        (
            "2. APPS COM PERMISSAO DE ADMINISTRADOR",
            ["dumpsys", "device_policy"],
            ADB_TIMEOUT_MEDIO
        ),
        (
            "3. SERVICOS DE ACESSIBILIDADE ATIVOS",
            ["settings", "get", "secure", "enabled_accessibility_services"],
            ADB_TIMEOUT_CURTO
        ),
        (
            "4. APPS COM PERMISSAO DE SOBREPOR A TELA",
            ["appops", "query-op", "SYSTEM_ALERT_WINDOW", "allow"],
            ADB_TIMEOUT_MEDIO
        ),
        (
            "5. PACOTES E PERMISSOES DO SISTEMA",
            ["dumpsys", "package"],
            ADB_TIMEOUT_LONGO
        ),
    ]

    for titulo, comando, timeout in comandos:
        resultado = adb_shell(comando, timeout=timeout)
        conteudo = resultado["stdout"]

        if resultado["stderr"].strip():
            conteudo += f"\n[ADB STDERR]\n{resultado['stderr']}"

        adicionar_secao(linhas, titulo, conteudo)

    linhas.extend([
        "=======================================================",
        "FIM DO RELATORIO - ASSISTENCIA TECNICA",
        "=======================================================",
    ])

    laudo_path = salvar_laudo("software", cliente, linhas)

    return {
        "raw_text": "\n".join(linhas),
        "laudo_path": laudo_path,
    }


def coletar_laudo_hardware(cliente: str, aparelho: str):
    linhas = montar_cabecalho_laudo(
        "LAUDO TECNICO DE HARDWARE E PLACA",
        cliente,
        aparelho
    )

    comandos = [
        (
            "1. INFORMACOES DO DISPOSITIVO",
            ["getprop"],
            ADB_TIMEOUT_MEDIO
        ),
        (
            "2. STATUS DE ENERGIA E BATERIA",
            ["dumpsys", "battery"],
            ADB_TIMEOUT_MEDIO
        ),
        (
            "3. SENSORES TERMICOS DA PLACA",
            ["dumpsys", "thermalservice"],
            ADB_TIMEOUT_MEDIO
        ),
        (
            "4. SENSORES DO APARELHO",
            ["dumpsys", "sensorservice"],
            ADB_TIMEOUT_LONGO
        ),
        (
            "5. LOGS DE CRASH",
            ["logcat", "-d", "-b", "crash"],
            ADB_TIMEOUT_LONGO
        ),
        (
            "6. LOGCAT GERAL",
            ["logcat", "-d"],
            ADB_TIMEOUT_LONGO
        ),
    ]

    for titulo, comando, timeout in comandos:
        resultado = adb_shell(comando, timeout=timeout)
        conteudo = resultado["stdout"]

        if resultado["stderr"].strip():
            conteudo += f"\n[ADB STDERR]\n{resultado['stderr']}"

        adicionar_secao(linhas, titulo, conteudo)

    linhas.extend([
        "=======================================================",
        "FIM DO RELATORIO - ASSISTENCIA TECNICA",
        "=======================================================",
    ])

    laudo_path = salvar_laudo("hardware", cliente, linhas)

    return {
        "raw_text": "\n".join(linhas),
        "laudo_path": laudo_path,
    }


# ======================================================
# ANÁLISE DE SOFTWARE
# ======================================================

def extrair_pacotes_terceiros(raw_text: str):
    pacotes = []
    dentro_secao = False

    for linha in raw_text.splitlines():
        linha_limpa = linha.strip()

        if "1. APLICATIVOS DE TERCEIROS INSTALADOS" in linha_limpa:
            dentro_secao = True
            continue

        if dentro_secao and linha_limpa.startswith("2. "):
            break

        if dentro_secao and linha_limpa.startswith("package:"):
            pacote = linha_limpa.replace("package:", "").strip()

            if pacote and pacote not in pacotes:
                pacotes.append(pacote)

    return pacotes


def analisar_software(raw_text: str):
    pacotes = extrair_pacotes_terceiros(raw_text)

    criticos = []
    suspeitos = []
    seguros = []
    permissoes_detectadas = []

    raw_lower = raw_text.lower()

    for permissao in PERMISSOES_CRITICAS:
        if permissao.lower() in raw_lower:
            permissoes_detectadas.append(permissao)

    for pacote in pacotes:
        pacote_lower = pacote.lower()

        if pacote in DICIONARIO_AMEACAS:
            info = DICIONARIO_AMEACAS[pacote]

            item = {
                "pacote": pacote,
                "nome": info["nome"],
                "explicacao": info["detalhe"],
                "risco": "Roubo de dados, monitoramento do aparelho, acesso remoto ou fraude.",
            }

            if info["status"] == "Ameaça Crítica":
                criticos.append(item)
            else:
                seguros.append({
                    "pacote": pacote,
                    "nome": info["nome"],
                    "explicacao": info["detalhe"],
                    "risco": "Nenhum risco conhecido.",
                })

            continue

        palavra_encontrada = None

        for palavra in PALAVRAS_SUSPEITAS:
            if palavra in pacote_lower:
                palavra_encontrada = palavra
                break

        if palavra_encontrada:
            suspeitos.append({
                "pacote": pacote,
                "nome": f"Possível app suspeito ({palavra_encontrada})",
                "explicacao": "O nome do pacote possui termo frequentemente usado por apps abusivos, adwares, rastreadores ou falsos utilitários.",
                "risco": "Pode causar anúncios abusivos, rastreamento, lentidão ou coleta de dados.",
            })
        else:
            seguros.append({
                "pacote": pacote,
                "nome": "Aplicativo de terceiro",
                "explicacao": "Aplicativo instalado pelo usuário. Deve ser validado com o cliente caso haja dúvida.",
                "risco": "Baixo, salvo se o cliente não reconhecer o aplicativo.",
            })

    alertas_total = len(criticos) + len(suspeitos)

    if criticos:
        resumo = f"Foram encontradas {len(criticos)} ameaça(s) crítica(s) e {len(suspeitos)} app(s) suspeito(s)."
    elif suspeitos:
        resumo = f"Nenhuma ameaça crítica conhecida, mas {len(suspeitos)} app(s) suspeito(s) exigem conferência."
    else:
        resumo = "Nenhuma ameaça crítica ou app suspeito foi identificado na análise inicial."

    return {
        "resumo": resumo,
        "alertas_total": alertas_total,
        "pacotes_total": len(pacotes),
        "criticos": criticos,
        "suspeitos": suspeitos,
        "seguros": seguros,
        "permissoes_detectadas": permissoes_detectadas,
    }


# ======================================================
# ANÁLISE DE HARDWARE
# ======================================================

def analisar_bateria(raw_text: str):
    secao_bateria = extrair_secao_laudo(
        raw_text,
        "2. STATUS DE ENERGIA E BATERIA",
        "3. SENSORES TERMICOS DA PLACA"
    )

    # Somente o estado atual. Não utiliza o histórico EventLogBuffer.
    estado_atual = secao_bateria.split("[EventLogBuffer]", 1)[0]

    dados = {}

    traducao_status = {
        "1": "Desconhecido",
        "2": "Carregando",
        "3": "Descarregando",
        "4": "Não carregando",
        "5": "Bateria cheia",
    }

    traducao_saude = {
        "1": "Desconhecida",
        "2": "Boa / saudável",
        "3": "Superaquecida",
        "4": "Morta / substituir",
        "5": "Sobretensão",
        "6": "Falha geral",
        "7": "Muito fria",
    }

    def buscar(padrao: str):
        match = re.search(
            padrao,
            estado_atual,
            flags=re.IGNORECASE | re.MULTILINE
        )

        return match.group(1).strip() if match else None

    nivel = buscar(r"^\s*level:\s*(\d+)\s*$")
    status = buscar(r"^\s*status:\s*(\d+)\s*$")
    saude = buscar(r"^\s*health:\s*(\d+)\s*$")
    voltagem = buscar(r"^\s*voltage:\s*(-?\d+)\s*$")
    temperatura = buscar(r"^\s*temperature:\s*(-?\d+)\s*$")
    tecnologia = buscar(r"^\s*technology:\s*(.+?)\s*$")

    if nivel is not None:
        dados["Nível de carga"] = f"{nivel}%"

    if status is not None:
        dados["Estado da carga"] = traducao_status.get(
            status,
            f"Código {status}"
        )

    if saude is not None:
        dados["Saúde da bateria"] = traducao_saude.get(
            saude,
            f"Código {saude}"
        )

    if voltagem is not None:
        dados["Voltagem"] = f"{float(voltagem) / 1000:.2f} V"

    if temperatura is not None:
        dados["Temperatura"] = (
            f"{float(temperatura) / 10:.1f} °C"
        )

    if tecnologia:
        dados["Tecnologia"] = tecnologia

    ciclo = buscar(r"^\s*cycle(?:_| )count:\s*(\d+)\s*$")

    if ciclo is not None:
        dados["Ciclos de carga"] = ciclo
    else:
        dados["Ciclos de carga"] = "Não informado pelo sistema"

    return dados


def analisar_hardware(raw_text: str):
    dados_bateria = analisar_bateria(raw_text)

    secao_crash = extrair_secao_laudo(
        raw_text,
        "5. LOGS DE CRASH",
        "6. LOGCAT GERAL"
    )

    secao_logcat = extrair_secao_laudo(
        raw_text,
        "6. LOGCAT GERAL"
    )

    linhas_logs = (
        secao_crash.splitlines()
        + secao_logcat.splitlines()
    )

    regras = [
        {
            "componente": "Sistema / Kernel",
            "titulo": "Kernel Panic",
            "gravidade": "Crítica",
            "padrao": r"\bkernel panic\b",
            "significado": (
                "O núcleo do Android registrou uma falha grave."
            ),
            "possiveis_causas": (
                "Falha de memória, armazenamento, alimentação, driver "
                "ou corrupção do sistema."
            ),
            "recomendacao": (
                "Confirmar reinícios relatados pelo cliente, verificar "
                "atualizações e executar testes de memória e placa."
            ),
        },
        {
            "componente": "Sistema",
            "titulo": "Watchdog com reinício forçado",
            "gravidade": "Crítica",
            "padrao": (
                r"(?:watchdog.*(?:killing system process|watchdog bite|"
                r"hard lockup|caused reboot))|"
                r"(?:(?:reset|reboot).*watchdog)"
            ),
            "significado": (
                "O monitor do sistema identificou um travamento real "
                "e iniciou ou solicitou a reinicialização."
            ),
            "possiveis_causas": (
                "Processo do sistema travado, driver defeituoso, falta "
                "de recursos ou instabilidade de hardware."
            ),
            "recomendacao": (
                "Cruzar o horário com reinícios percebidos pelo cliente "
                "e investigar os processos citados nas evidências."
            ),
        },
        {
            "componente": "Temperatura",
            "titulo": "Desligamento térmico",
            "gravidade": "Crítica",
            "padrao": r"\bthermal[_ ]shutdown\b",
            "significado": (
                "O aparelho registrou desligamento de proteção por "
                "temperatura excessiva."
            ),
            "possiveis_causas": (
                "Bateria, processador, circuito de carga, dissipação "
                "ou uso intenso em ambiente quente."
            ),
            "recomendacao": (
                "Testar temperaturas em repouso e em carga, verificando "
                "bateria, carregador e dissipação térmica."
            ),
        },
        {
            "componente": "Sistema / Aplicativo",
            "titulo": "Falha nativa de processo",
            "gravidade": "Alta",
            "padrao": r"\bfatal signal\b",
            "significado": (
                "Um processo nativo foi encerrado de forma inesperada."
            ),
            "possiveis_causas": (
                "Bug de software, biblioteca incompatível, driver ou "
                "instabilidade de memória."
            ),
            "recomendacao": (
                "Identificar o processo nas evidências e verificar se a "
                "falha se repete durante o uso."
            ),
        },
        {
            "componente": "Android / Aplicativo",
            "titulo": "Exceção fatal",
            "gravidade": "Moderada",
            "padrao": r"\bfatal exception\b",
            "significado": (
                "Um aplicativo ou serviço encerrou por erro."
            ),
            "possiveis_causas": (
                "Falha do aplicativo, dados corrompidos ou "
                "incompatibilidade de software."
            ),
            "recomendacao": (
                "Verificar qual aplicativo aparece na evidência antes "
                "de relacionar o evento a uma falha física."
            ),
        },
        {
            "componente": "Android / Aplicativo",
            "titulo": "Aplicativo sem resposta",
            "gravidade": "Moderada",
            "padrao": r"\bANR in\b",
            "significado": (
                "Um aplicativo deixou de responder temporariamente."
            ),
            "possiveis_causas": (
                "Aplicativo sobrecarregado, armazenamento lento, pouca "
                "memória disponível ou falha de software."
            ),
            "recomendacao": (
                "Identificar o aplicativo e verificar frequência e "
                "impacto percebido pelo usuário."
            ),
        },
        {
            "componente": "Câmera",
            "titulo": "Erro de câmera",
            "gravidade": "Alta",
            "padrao": (
                r"(?=.*\b(?:camera|cameraserver|camera3-device)\b)"
                r"(?=.*\b(?:fatal|failed|failure|error|"
                r"not responding|dead object)\b)"
            ),
            "significado": (
                "Um serviço relacionado à câmera registrou falha."
            ),
            "possiveis_causas": (
                "Aplicativo, serviço da câmera, módulo, flex ou "
                "comunicação com o componente."
            ),
            "recomendacao": (
                "Testar todas as câmeras e modos. Não condenar o módulo "
                "sem reproduzir o problema."
            ),
        },
        {
            "componente": "Biometria",
            "titulo": "Erro no leitor biométrico",
            "gravidade": "Alta",
            "padrao": (
                r"(?=.*\b(?:fingerprint|biometric)\b)"
                r"(?=.*\b(?:fatal|failed|failure|error|"
                r"not responding|unavailable)\b)"
            ),
            "significado": (
                "O serviço biométrico encontrou falha de comunicação "
                "ou funcionamento."
            ),
            "possiveis_causas": (
                "Software, sensor biométrico, flex, tela incompatível "
                "ou falha de calibração."
            ),
            "recomendacao": (
                "Testar cadastro e leitura da digital e verificar se "
                "houve troca de tela."
            ),
        },
        {
            "componente": "Tela / Touch",
            "titulo": "Erro de tela ou toque",
            "gravidade": "Alta",
            "padrao": (
                r"(?=.*\b(?:touchscreen|touchpanel|touch driver|"
                r"display driver)\b)"
                r"(?=.*\b(?:fatal|failed|failure|error|"
                r"not responding|timeout)\b)"
            ),
            "significado": (
                "O sistema registrou falha relacionada ao controlador "
                "da tela ou do toque."
            ),
            "possiveis_causas": (
                "Tela, flex, conector, controlador, driver ou peça "
                "incompatível."
            ),
            "recomendacao": (
                "Executar teste manual de toque em toda a tela e "
                "inspecionar conexões antes de concluir o defeito."
            ),
        },
        {
            "componente": "Armazenamento",
            "titulo": "Erro de leitura ou gravação",
            "gravidade": "Crítica",
            "padrao": (
                r"\b(?:i/o error|filesystem corruption|"
                r"ext4-fs error|f2fs.*error|ufs.*fatal)\b"
            ),
            "significado": (
                "Foi registrado erro relacionado ao armazenamento."
            ),
            "possiveis_causas": (
                "Sistema de arquivos corrompido, memória interna "
                "degradada ou falha de alimentação."
            ),
            "recomendacao": (
                "Fazer backup, verificar recorrência e testar o "
                "armazenamento antes de qualquer restauração."
            ),
        },
    ]

    achados = []

    for regra in regras:
        padrao = re.compile(
            regra["padrao"],
            flags=re.IGNORECASE
        )

        evidencias = []

        for linha in linhas_logs:
            linha_limpa = linha.strip()

            if not linha_limpa or len(linha_limpa) > 1200:
                continue

            linha_lower = linha_limpa.lower()

            if any(ruido in linha_lower for ruido in [
                "result=ok",
                "errors: 0",
                "error=0",
                "no error",
                "watchdog thread idle",
                "watchdog timeout set",
                "cameraservicewatchdog::watchthread",
                "init.svc.watchdogd",
            ]):
                continue

            if padrao.search(linha_limpa):
                evidencias.append(linha_limpa)

        if evidencias:
            achado = {
                "componente": regra["componente"],
                "titulo": regra["titulo"],
                "gravidade": regra["gravidade"],
                "quantidade": len(evidencias),
                "significado": regra["significado"],
                "possiveis_causas": regra["possiveis_causas"],
                "recomendacao": regra["recomendacao"],
                "evidencias": evidencias[:3],
            }

            achados.append(achado)

    saude = dados_bateria.get("Saúde da bateria", "").lower()

    if any(estado in saude for estado in [
        "superaquecida",
        "morta",
        "sobretensão",
        "falha geral",
        "muito fria",
    ]):
        achados.append({
            "componente": "Bateria",
            "titulo": "Saúde anormal da bateria",
            "gravidade": "Alta",
            "quantidade": 1,
            "significado": (
                "O próprio Android classificou a saúde da bateria "
                "como anormal."
            ),
            "possiveis_causas": (
                "Bateria degradada, temperatura extrema ou falha no "
                "circuito de carga."
            ),
            "recomendacao": (
                "Confirmar com medição e teste de carga antes da troca."
            ),
            "evidencias": [
                dados_bateria.get("Saúde da bateria")
            ],
        })

    temperatura = dados_bateria.get("Temperatura", "")
    temp_match = re.search(r"([\d.,]+)", temperatura)

    if temp_match:
        temperatura_valor = float(
            temp_match.group(1).replace(",", ".")
        )

        if temperatura_valor >= 45:
            gravidade = (
                "Alta"
                if temperatura_valor >= 50
                else "Moderada"
            )

            achados.append({
                "componente": "Bateria",
                "titulo": "Temperatura elevada da bateria",
                "gravidade": gravidade,
                "quantidade": 1,
                "significado": (
                    "A bateria estava aquecida no momento da coleta."
                ),
                "possiveis_causas": (
                    "Carregamento, uso intenso, ambiente quente, "
                    "bateria degradada ou circuito de carga."
                ),
                "recomendacao": (
                    "Repetir o teste em repouso. Uma leitura isolada "
                    "durante carregamento não confirma defeito."
                ),
                "evidencias": [temperatura],
            })

    ocorrencias_total = sum(
        achado["quantidade"]
        for achado in achados
    )

    gravidades = {
        achado["gravidade"]
        for achado in achados
    }

    if "Crítica" in gravidades or "Alta" in gravidades:
        status_geral = "requer_atencao"
        resumo = (
            f"Foram identificadas {len(achados)} situação(ões) que "
            "merecem verificação técnica. Os registros são evidências "
            "e devem ser confirmados com testes práticos."
        )

    elif achados:
        status_geral = "observacao"
        resumo = (
            f"Foram identificadas {len(achados)} situação(ões) de "
            "software ou funcionamento para conferência."
        )

    else:
        status_geral = "sem_indicios"
        resumo = (
            "Nenhum indício consistente de falha de hardware foi "
            "encontrado nos registros analisados."
        )

    return {
        "resumo": resumo,
        "status_geral": status_geral,
        "alertas_total": len(achados),
        "ocorrencias_total": ocorrencias_total,
        "dados_bateria": dados_bateria,
        "achados": achados,
    }


# ======================================================
# EXECUÇÃO COMPLETA
# ======================================================

def executar_diagnostico_software(
    cliente: str,
    aparelho: str,
    identificacao_adb: dict | None = None
):
    cliente = cliente.strip() or "Não informado"
    aparelho = aparelho.strip()

    conexao = verificar_dispositivo_adb()

    if not conexao["ok"]:
        return {
            "id": str(uuid.uuid4()),
            "tipo": "software",
            "cliente": cliente,
            "aparelho": aparelho,
            "status": "erro",
            "resumo": conexao["mensagem"],
            "alertas_total": 0,
            "resultado_json": {
                "conexao": conexao,
            },
            "laudo_path": None,
            "erro": conexao["detalhe"],
            "created_at": agora_iso(),
        }

    identificacao = (
        identificacao_adb
        or coletar_identificacao_aparelho_adb()
    )

    if not aparelho:
        aparelho = montar_nome_aparelho(identificacao)

    coleta = coletar_laudo_software(cliente, aparelho)
    analise = analisar_software(coleta["raw_text"])

    analise["identificacao_adb"] = identificacao

    return {
        "id": str(uuid.uuid4()),
        "tipo": "software",
        "cliente": cliente,
        "aparelho": aparelho,
        "status": "concluido",
        "resumo": analise["resumo"],
        "alertas_total": analise["alertas_total"],
        "resultado_json": analise,
        "laudo_path": coleta["laudo_path"],
        "erro": None,
        "created_at": agora_iso(),
    }

def executar_diagnostico_hardware(
    cliente: str,
    aparelho: str,
    identificacao_adb: dict | None = None
):
    cliente = cliente.strip() or "Não informado"
    aparelho = aparelho.strip()

    conexao = verificar_dispositivo_adb()

    if not conexao["ok"]:
        return {
            "id": str(uuid.uuid4()),
            "tipo": "hardware",
            "cliente": cliente,
            "aparelho": aparelho,
            "status": "erro",
            "resumo": conexao["mensagem"],
            "alertas_total": 0,
            "resultado_json": {
                "conexao": conexao,
            },
            "laudo_path": None,
            "erro": conexao["detalhe"],
            "created_at": agora_iso(),
        }

    identificacao = (
        identificacao_adb
        or coletar_identificacao_aparelho_adb()
    )

    if not aparelho:
        aparelho = montar_nome_aparelho(identificacao)

    coleta = coletar_laudo_hardware(cliente, aparelho)
    analise = analisar_hardware(coleta["raw_text"])

    analise["identificacao_adb"] = identificacao

    return {
        "id": str(uuid.uuid4()),
        "tipo": "hardware",
        "cliente": cliente,
        "aparelho": aparelho,
        "status": "concluido",
        "resumo": analise["resumo"],
        "alertas_total": analise["alertas_total"],
        "resultado_json": analise,
        "laudo_path": coleta["laudo_path"],
        "erro": None,
        "created_at": agora_iso(),
    }