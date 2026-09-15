"""
Carregador seguro de documentos da camada RAG
do Agentic SOC N1 Lab.

Fase 5.1 — Ingestão segura de conhecimento.

Responsabilidades:

- localizar documentos internos autorizados;
- validar caminhos;
- bloquear acesso fora de knowledge/;
- identificar o tipo de conhecimento;
- limitar extensões permitidas;
- limitar tamanho de arquivos;
- preservar metadados da fonte;
- produzir RAGDocument.

Estrutura autorizada:

knowledge/
├── mitre/
├── playbooks/
├── policies/
└── runbooks/

Princípios:

- leitura local;
- nenhum acesso externo;
- nenhum path traversal;
- nenhum arquivo executável;
- nenhum segredo;
- nenhuma modificação do documento de origem;
- fail-closed para entradas inválidas.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from rag.config import RAGConfig
from rag.contracts import RAGDocument


SUPPORTED_DOCUMENT_EXTENSIONS: tuple[str, ...] = (
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
)


KNOWLEDGE_DIRECTORY_TYPE_MAP: dict[str, str] = {
    "mitre": "mitre",
    "playbooks": "playbook",
    "policies": "policy",
    "runbooks": "runbook",
}


MAX_DOCUMENT_BYTES = (
    2 * 1024 * 1024
)


class RAGDocumentLoader:
    """
    Carrega documentos autorizados
    da base local de conhecimento.
    """

    def __init__(
        self,
        config: RAGConfig | None = None,
        *,
        project_root: str | Path | None = None,
    ) -> None:
        """
        Inicializa o loader.

        project_root é opcional e existe
        principalmente para testes controlados.
        """

        self._config = (
            config
            if config is not None
            else RAGConfig()
        )

        if project_root is None:
            self._project_root = (
                Path(__file__)
                .resolve()
                .parents[2]
            )

        else:
            self._project_root = (
                Path(project_root)
                .expanduser()
                .resolve()
            )

        self._knowledge_root = (
            self._project_root
            / self._config.knowledge_directory
        ).resolve()

        self._validate_knowledge_root()

    @property
    def config(
        self,
    ) -> RAGConfig:
        """
        Retorna configuração RAG.
        """

        return self._config

    @property
    def project_root(
        self,
    ) -> Path:
        """
        Retorna raiz do projeto.
        """

        return self._project_root

    @property
    def knowledge_root(
        self,
    ) -> Path:
        """
        Retorna raiz autorizada
        da base de conhecimento.
        """

        return self._knowledge_root

    def load_all(
        self,
    ) -> list[RAGDocument]:
        """
        Carrega todos os documentos suportados
        das quatro bases oficiais.

        Arquivos desconhecidos são ignorados.
        """

        documents: list[
            RAGDocument
        ] = []

        for directory_name in (
            KNOWLEDGE_DIRECTORY_TYPE_MAP
        ):
            directory = (
                self._knowledge_root
                / directory_name
            )

            if not directory.exists():
                continue

            if not directory.is_dir():
                raise ValueError(
                    "Estrutura de conhecimento "
                    "inválida: "
                    f"{directory_name!r} "
                    "não é um diretório."
                )

            for path in sorted(
                directory.rglob("*")
            ):
                if not path.is_file():
                    continue

                if path.is_symlink():
                    continue

                if (
                    path.suffix.lower()
                    not in SUPPORTED_DOCUMENT_EXTENSIONS
                ):
                    continue

                documents.append(
                    self.load_file(
                        path
                    )
                )

        return documents

    def load_file(
        self,
        file_path: str | Path,
    ) -> RAGDocument:
        """
        Carrega um documento específico
        da base autorizada.
        """

        raw_path = Path(
            file_path
        ).expanduser()

        if raw_path.is_absolute():
            candidate = raw_path

        else:
            candidate = (
                self._project_root
                / raw_path
            )

        if candidate.is_symlink():
            raise PermissionError(
                "Links simbólicos não são "
                "permitidos na ingestão RAG."
            )

        resolved_path = (
            candidate.resolve()
        )

        self._ensure_inside_knowledge_root(
            resolved_path
        )

        if not resolved_path.exists():
            raise FileNotFoundError(
                "Documento de conhecimento "
                "não encontrado."
            )

        if not resolved_path.is_file():
            raise ValueError(
                "O caminho informado não "
                "é um arquivo."
            )

        extension = (
            resolved_path.suffix.lower()
        )

        if (
            extension
            not in SUPPORTED_DOCUMENT_EXTENSIONS
        ):
            raise ValueError(
                "Extensão de documento "
                "não autorizada para o RAG: "
                f"{extension!r}."
            )

        size_bytes = (
            resolved_path.stat().st_size
        )

        if (
            size_bytes
            > MAX_DOCUMENT_BYTES
        ):
            raise ValueError(
                "Documento excede o tamanho "
                "máximo permitido pelo RAG."
            )

        try:
            content = (
                resolved_path.read_text(
                    encoding="utf-8"
                )
            )

        except UnicodeDecodeError as exc:
            raise ValueError(
                "Documento precisa utilizar "
                "codificação UTF-8."
            ) from exc

        content = content.strip()

        if not content:
            raise ValueError(
                "Documento de conhecimento "
                "não pode estar vazio."
            )

        document_type = (
            self._document_type_from_path(
                resolved_path
            )
        )

        source_path = (
            resolved_path
            .relative_to(
                self._project_root
            )
            .as_posix()
        )

        document_id = (
            self._create_document_id(
                source_path
            )
        )

        return RAGDocument(
            document_id=document_id,
            document_name=(
                resolved_path.name
            ),
            document_type=(
                document_type
            ),
            source_path=source_path,
            content=content,
            metadata={
                "extension": extension,
                "size_bytes": (
                    size_bytes
                ),
                "local_source": True,
                "read_only": True,
            },
        )

    def _validate_knowledge_root(
        self,
    ) -> None:
        """
        Garante que knowledge/
        permanece dentro do projeto.
        """

        if not self._is_relative_to(
            self._knowledge_root,
            self._project_root,
        ):
            raise PermissionError(
                "knowledge_directory precisa "
                "permanecer dentro do projeto."
            )

    def _ensure_inside_knowledge_root(
        self,
        path: Path,
    ) -> None:
        """
        Bloqueia qualquer arquivo
        fora de knowledge/.
        """

        if not self._is_relative_to(
            path,
            self._knowledge_root,
        ):
            raise PermissionError(
                "Acesso fora da base "
                "knowledge/ foi bloqueado."
            )

    def _document_type_from_path(
        self,
        path: Path,
    ) -> str:
        """
        Descobre o tipo oficial do documento
        pela primeira pasta abaixo de knowledge/.
        """

        relative = path.relative_to(
            self._knowledge_root
        )

        if not relative.parts:
            raise ValueError(
                "Documento sem categoria "
                "de conhecimento."
            )

        directory_name = (
            relative.parts[0]
            .strip()
            .lower()
        )

        document_type = (
            KNOWLEDGE_DIRECTORY_TYPE_MAP
            .get(
                directory_name
            )
        )

        if document_type is None:
            raise ValueError(
                "Documento fora das categorias "
                "oficiais do RAG."
            )

        return document_type

    @staticmethod
    def _create_document_id(
        source_path: str,
    ) -> str:
        """
        Gera ID determinístico a partir
        do caminho relativo do documento.
        """

        digest = sha256(
            source_path.encode(
                "utf-8"
            )
        ).hexdigest()

        return (
            "DOC-"
            + digest[:16].upper()
        )

    @staticmethod
    def _is_relative_to(
        path: Path,
        parent: Path,
    ) -> bool:
        """
        Verifica containment de caminho
        sem depender de comparação textual.
        """

        try:
            path.relative_to(
                parent
            )

        except ValueError:
            return False

        return True

    def safe_summary(
        self,
    ) -> dict[str, object]:
        """
        Retorna resumo seguro do loader.
        """

        return {
            "integration": (
                "RAG_INGESTION"
            ),
            "knowledge_directory": (
                self._config
                .knowledge_directory
            ),
            "supported_extensions": (
                SUPPORTED_DOCUMENT_EXTENSIONS
            ),
            "max_document_bytes": (
                MAX_DOCUMENT_BYTES
            ),
            "knowledge_types": tuple(
                KNOWLEDGE_DIRECTORY_TYPE_MAP
                .values()
            ),
            "local_only": True,
            "read_only": True,
        }