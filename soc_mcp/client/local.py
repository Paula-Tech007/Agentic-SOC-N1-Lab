"""
Cliente MCP local
do Agentic SOC N1 Lab.

Fase 6.1 — Cliente/uso controlado do MCP.

Responsabilidades atuais:

- conectar localmente a um MCPServer
  já criado pelo projeto;
- utilizar o Client oficial do SDK MCP;
- preservar o ciclo de vida assíncrono;
- impedir utilização fora de uma sessão ativa;
- listar somente tools publicadas
  pelo servidor MCP atual;
- converter tools publicadas para
  contratos próprios do cliente;
- validar se uma tool continua publicada
  antes de solicitar sua execução;
- executar uma tool read-only publicada
  pelo servidor MCP;
- converter resultado MCP para
  MCPToolCallResult;
- não selecionar agent_id;
- não selecionar case_id;
- não selecionar correlation_id;
- não criar transporte de rede;
- não executar ações críticas;
- não substituir ToolRuntime;
- manter fail-closed.

O contexto de segurança continua pertencendo
ao servidor MCP criado por create_mcp_server().

O cliente não decide quais tools um agente
pode utilizar.

A autorização continua sendo aplicada por:

MCPServer
    ↓
MCPToolRegistry
    ↓
MCPToolRuntimeBridge
    ↓
ToolRuntime

A checagem realizada pelo cliente utiliza
somente a lista efetivamente publicada pelo
servidor MCP atual.

Ela não substitui nenhuma validação
server-side.

O encerramento da sessão MCP é realizado
como fechamento normal.

Exceções da camada cliente não são entregues
ao TaskGroup interno do SDK MCP durante
o encerramento da conexão.

A exceção original continua sendo propagada
ao chamador pelo contexto assíncrono.

Princípio:

    A LLM interpreta;
    a ferramenta comprova.
"""

from __future__ import annotations

from collections.abc import (
    Mapping,
)

from typing import (
    Any,
)

from mcp import (
    Client,
)

from mcp.server import (
    MCPServer,
)

from soc_mcp.client.contracts import (
    MCPClientToolCallRequest,
    MCPClientToolDescriptor,
)

from soc_mcp.contracts import (
    MCPToolCallResult,
)


def _tool_required_string(
    value: object,
    *,
    field_name: str,
) -> str:
    """
    Valida uma string obrigatória
    recebida do SDK MCP.

    Dados inesperados recebidos pela
    sessão devem falhar fechado.
    """

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            f"{field_name} retornado pelo "
            "servidor MCP precisa ser "
            "uma string."
        )

    cleaned = value.strip()

    if not cleaned:
        raise RuntimeError(
            f"{field_name} retornado pelo "
            "servidor MCP não pode "
            "ser vazio."
        )

    return cleaned


def _tool_optional_string(
    value: object,
    *,
    field_name: str,
) -> str | None:
    """
    Valida uma string opcional
    recebida do SDK MCP.
    """

    if value is None:
        return None

    return _tool_required_string(
        value,
        field_name=field_name,
    )


def _tool_input_schema(
    tool: object,
) -> Mapping[str, Any]:
    """
    Obtém o schema de entrada
    apresentado pelo SDK MCP.

    O SDK utiliza inputSchema.

    O fallback para input_schema
    existe somente para preservar
    compatibilidade de representação
    sem alterar política de segurança.

    Schema ausente ou inválido
    falha fechado.
    """

    schema = getattr(
        tool,
        "inputSchema",
        None,
    )

    if schema is None:
        schema = getattr(
            tool,
            "input_schema",
            None,
        )

    if schema is None:
        raise RuntimeError(
            "Tool retornada pelo servidor MCP "
            "não possui inputSchema."
        )

    if not isinstance(
        schema,
        Mapping,
    ):
        raise RuntimeError(
            "inputSchema retornado pelo "
            "servidor MCP precisa ser "
            "um mapping."
        )

    return schema


def _tool_to_descriptor(
    tool: object,
) -> MCPClientToolDescriptor:
    """
    Converte uma tool apresentada
    pelo SDK MCP para o contrato
    próprio da camada cliente.

    Nenhum contexto de segurança
    é criado ou alterado aqui.
    """

    if not hasattr(
        tool,
        "name",
    ):
        raise RuntimeError(
            "Tool retornada pelo servidor MCP "
            "não possui name."
        )

    tool_id = _tool_required_string(
        getattr(
            tool,
            "name",
        ),
        field_name="tool.name",
    )

    title = _tool_optional_string(
        getattr(
            tool,
            "title",
            None,
        ),
        field_name="tool.title",
    )

    description = _tool_optional_string(
        getattr(
            tool,
            "description",
            None,
        ),
        field_name="tool.description",
    )

    input_schema = _tool_input_schema(
        tool
    )

    return MCPClientToolDescriptor(
        tool_id=tool_id,
        title=title,
        description=description,
        input_schema=input_schema,
    )


def _required_payload_mapping(
    payload: Mapping[str, Any],
    *,
    field_name: str,
) -> Mapping[str, Any]:
    """
    Obtém um mapping obrigatório
    do payload estruturado MCP.
    """

    if field_name not in payload:
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"campo ausente {field_name}."
        )

    value = payload[
        field_name
    ]

    if not isinstance(
        value,
        Mapping,
    ):
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"{field_name} precisa "
            "ser um mapping."
        )

    return value


def _required_payload_string(
    payload: Mapping[str, Any],
    *,
    field_name: str,
) -> str:
    """
    Obtém uma string obrigatória
    do payload estruturado MCP.
    """

    if field_name not in payload:
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"campo ausente {field_name}."
        )

    return _tool_required_string(
        payload[
            field_name
        ],
        field_name=field_name,
    )


def _optional_payload_string(
    payload: Mapping[str, Any],
    *,
    field_name: str,
) -> str | None:
    """
    Obtém string opcional
    do payload estruturado MCP.
    """

    value = payload.get(
        field_name
    )

    return _tool_optional_string(
        value,
        field_name=field_name,
    )


def _required_payload_bool(
    payload: Mapping[str, Any],
    *,
    field_name: str,
) -> bool:
    """
    Obtém booleano obrigatório
    do payload estruturado MCP.
    """

    if field_name not in payload:
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"campo ausente {field_name}."
        )

    value = payload[
        field_name
    ]

    if not isinstance(
        value,
        bool,
    ):
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"{field_name} precisa "
            "ser booleano."
        )

    return value


def _required_payload_int(
    payload: Mapping[str, Any],
    *,
    field_name: str,
) -> int:
    """
    Obtém inteiro não negativo
    do payload estruturado MCP.
    """

    if field_name not in payload:
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"campo ausente {field_name}."
        )

    value = payload[
        field_name
    ]

    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
    ):
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"{field_name} precisa "
            "ser inteiro."
        )

    if value < 0:
        raise RuntimeError(
            "Resultado MCP inválido: "
            f"{field_name} não pode "
            "ser negativo."
        )

    return value


def _structured_content_to_result(
    payload: object,
) -> MCPToolCallResult:
    """
    Converte structured_content
    devolvido pelo SDK MCP para
    MCPToolCallResult.

    A conversão é fail-closed:
    campos obrigatórios ausentes
    ou inválidos causam erro.
    """

    if not isinstance(
        payload,
        Mapping,
    ):
        raise RuntimeError(
            "structured_content retornado "
            "pelo MCP precisa ser "
            "um mapping."
        )

    request_id = (
        _required_payload_string(
            payload,
            field_name="request_id",
        )
    )

    execution_id = (
        _required_payload_string(
            payload,
            field_name="execution_id",
        )
    )

    agent_id = (
        _required_payload_string(
            payload,
            field_name="agent_id",
        )
    )

    case_id = (
        _required_payload_string(
            payload,
            field_name="case_id",
        )
    )

    correlation_id = (
        _required_payload_string(
            payload,
            field_name="correlation_id",
        )
    )

    tool_id = (
        _required_payload_string(
            payload,
            field_name="tool_id",
        )
    )

    status = (
        _required_payload_string(
            payload,
            field_name="status",
        )
    )

    success = (
        _required_payload_bool(
            payload,
            field_name="success",
        )
    )

    output = (
        _required_payload_mapping(
            payload,
            field_name="output",
        )
    )

    evidence = (
        _required_payload_mapping(
            payload,
            field_name="evidence",
        )
    )

    error_code = (
        _optional_payload_string(
            payload,
            field_name="error_code",
        )
    )

    error_message = (
        _optional_payload_string(
            payload,
            field_name="error_message",
        )
    )

    attempts = (
        _required_payload_int(
            payload,
            field_name="attempts",
        )
    )

    duration_ms = (
        _required_payload_int(
            payload,
            field_name="duration_ms",
        )
    )

    return MCPToolCallResult(
        request_id=request_id,
        execution_id=execution_id,
        agent_id=agent_id,
        case_id=case_id,
        correlation_id=correlation_id,
        tool_id=tool_id,
        status=status,
        success=success,
        output=output,
        evidence=evidence,
        error_code=error_code,
        error_message=error_message,
        attempts=attempts,
        duration_ms=duration_ms,
    )


class LocalMCPClient:
    """
    Cliente local e controlado
    para um MCPServer do projeto.

    Responsabilidades desta classe:

    - abrir e fechar a sessão MCP;
    - impedir uso fora da sessão;
    - listar tools publicadas
      pelo servidor MCP;
    - converter metadados das tools
      para contratos locais seguros;
    - verificar se a tool solicitada
      continua publicada pelo servidor;
    - executar tool read-only publicada;
    - converter structured_content para
      MCPToolCallResult.

    Esta classe NÃO permite:

    - seleção de agente;
    - seleção de caso;
    - seleção de correlation_id;
    - transporte de rede.

    A permissão das tools não é decidida
    pelo cliente.

    O servidor registra somente
    ferramentas previamente autorizadas
    para seu agente vinculado.
    """

    def __init__(
        self,
        server: MCPServer,
    ) -> None:
        """
        Inicializa o cliente local.

        O servidor recebido já deve ter
        sido criado pela camada oficial
        soc_mcp.server.create_mcp_server().
        """

        if not isinstance(
            server,
            MCPServer,
        ):
            raise TypeError(
                "server precisa ser "
                "uma instância de MCPServer."
            )

        self._server = server

        self._client: Client | None = None

        self._connected = False

    @property
    def server(
        self,
    ) -> MCPServer:
        """
        Retorna o servidor MCP
        associado ao cliente.
        """

        return self._server

    @property
    def connected(
        self,
    ) -> bool:
        """
        Indica se existe uma sessão
        MCP ativa.
        """

        return self._connected

    @property
    def session(
        self,
    ) -> Client:
        """
        Retorna a sessão MCP ativa.

        Falha fechado caso o código
        tente utilizar o cliente antes
        da abertura da conexão.
        """

        client = self._client

        if (
            not self._connected
            or client is None
        ):
            raise RuntimeError(
                "Cliente MCP local "
                "não está conectado."
            )

        return client

    async def connect(
        self,
    ) -> LocalMCPClient:
        """
        Abre uma sessão MCP local.

        Conexões duplicadas são
        rejeitadas para manter um ciclo
        de vida explícito e previsível.
        """

        if self._connected:
            raise RuntimeError(
                "Cliente MCP local "
                "já está conectado."
            )

        client = Client(
            self._server
        )

        try:
            await client.__aenter__()

        except Exception:
            self._client = None
            self._connected = False
            raise

        self._client = client
        self._connected = True

        return self

    async def close(
        self,
    ) -> None:
        """
        Encerra a sessão MCP local.

        Chamar close() sem uma conexão
        ativa não produz efeito.
        """

        client = self._client

        if (
            not self._connected
            or client is None
        ):
            self._client = None
            self._connected = False
            return

        try:
            await client.__aexit__(
                None,
                None,
                None,
            )

        finally:
            self._client = None
            self._connected = False

    async def list_authorized_tools(
        self,
    ) -> tuple[MCPClientToolDescriptor, ...]:
        """
        Lista somente as tools publicadas
        pelo MCPServer atual.

        O cliente não calcula permissões.

        create_mcp_server() já registra
        somente as tools autorizadas para
        o agente vinculado ao servidor.

        A resposta do SDK é convertida
        para contratos imutáveis próprios.

        Respostas malformadas ou tools
        duplicadas falham fechado.
        """

        client = self.session

        response = await client.list_tools()

        if not hasattr(
            response,
            "tools",
        ):
            raise RuntimeError(
                "Resposta list_tools do MCP "
                "não possui tools."
            )

        raw_tools = getattr(
            response,
            "tools",
        )

        if not isinstance(
            raw_tools,
            (list, tuple),
        ):
            raise RuntimeError(
                "tools retornado pelo MCP "
                "precisa ser uma coleção."
            )

        descriptors: list[
            MCPClientToolDescriptor
        ] = []

        seen_tool_ids: set[str] = set()

        for tool in raw_tools:
            descriptor = (
                _tool_to_descriptor(
                    tool
                )
            )

            if (
                descriptor.tool_id
                in seen_tool_ids
            ):
                raise RuntimeError(
                    "Servidor MCP retornou "
                    "tool duplicada: "
                    f"{descriptor.tool_id}."
                )

            seen_tool_ids.add(
                descriptor.tool_id
            )

            descriptors.append(
                descriptor
            )

        descriptors.sort(
            key=lambda item: item.tool_id
        )

        return tuple(
            descriptors
        )

    async def _ensure_tool_is_published(
        self,
        tool_id: str,
    ) -> None:
        """
        Confirma que a tool solicitada
        está atualmente publicada pelo
        MCPServer vinculado ao cliente.

        A lista do próprio servidor é
        utilizada como fonte da decisão.

        Esta checagem não substitui
        autorização server-side.

        Tool ausente falha fechado antes
        de call_tool().
        """

        normalized_tool_id = (
            _tool_required_string(
                tool_id,
                field_name="tool_id",
            )
        )

        tools = (
            await self.list_authorized_tools()
        )

        published_tool_ids = {
            tool.tool_id
            for tool
            in tools
        }

        if (
            normalized_tool_id
            not in published_tool_ids
        ):
            raise RuntimeError(
                "Tool MCP não autorizada "
                "ou não publicada pelo "
                "servidor atual: "
                f"{normalized_tool_id}."
            )

    async def execute_read_only_tool(
        self,
        request: MCPClientToolCallRequest,
    ) -> MCPToolCallResult:
        """
        Executa uma tool publicada
        pelo MCPServer atual.

        Antes da chamada, o cliente
        confirma que a tool consta
        atualmente na lista publicada
        pelo próprio servidor.

        O cliente envia somente:

        - tool_id;
        - argumentos funcionais.

        agent_id, case_id e correlation_id
        permanecem vinculados ao servidor.

        O ToolRuntime continua soberano.

        A checagem client-side não substitui
        as validações do servidor, bridge
        ou ToolRuntime.
        """

        if not isinstance(
            request,
            MCPClientToolCallRequest,
        ):
            raise TypeError(
                "request precisa ser "
                "MCPClientToolCallRequest."
            )

        client = self.session

        await self._ensure_tool_is_published(
            request.tool_id
        )

        result = await client.call_tool(
            request.tool_id,
            {
                "arguments": dict(
                    request.arguments
                )
            },
        )

        is_error = getattr(
            result,
            "is_error",
            None,
        )

        if not isinstance(
            is_error,
            bool,
        ):
            raise RuntimeError(
                "Resultado call_tool do MCP "
                "não possui is_error "
                "booleano válido."
            )

        structured_content = getattr(
            result,
            "structured_content",
            None,
        )

        if structured_content is None:
            raise RuntimeError(
                "Resultado call_tool do MCP "
                "não possui "
                "structured_content."
            )

        converted = (
            _structured_content_to_result(
                structured_content
            )
        )

        if is_error:
            if converted.success:
                raise RuntimeError(
                    "Resultado MCP inconsistente: "
                    "is_error=True com "
                    "success=True."
                )

        else:
            if not converted.success:
                raise RuntimeError(
                    "Resultado MCP inconsistente: "
                    "is_error=False com "
                    "success=False."
                )

        if (
            converted.tool_id
            != request.tool_id
        ):
            raise RuntimeError(
                "Resultado MCP pertence "
                "a uma tool diferente "
                "da solicitada."
            )

        return converted

    async def __aenter__(
        self,
    ) -> LocalMCPClient:
        """
        Permite uso com:

            async with LocalMCPClient(...)
        """

        return await self.connect()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> bool:
        """
        Encerra a sessão MCP ao sair
        do contexto assíncrono.

        A sessão interna é sempre fechada
        como encerramento normal.

        A exceção original do bloco chamador
        não é enviada ao TaskGroup interno
        do SDK MCP.

        Como este método retorna False,
        a exceção original continua sendo
        propagada normalmente ao chamador.
        """

        client = self._client

        if (
            not self._connected
            or client is None
        ):
            self._client = None
            self._connected = False
            return False

        try:
            await client.__aexit__(
                None,
                None,
                None,
            )

        finally:
            self._client = None
            self._connected = False

        return False