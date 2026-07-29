import sqlite3
from pathlib import Path
from datetime import datetime


DB_ANTIGO = Path(
    r"C:\Users\Win10\Documents\Workspace\BestSystem\bestsystem.db"
)

DB_NOVO = Path(
    r"C:\Users\Win10\Documents\Workspace\System\bestsystem.db"
)


# A ordem respeita as chaves estrangeiras.
TABELAS_MIGRACAO = [
    "sales",
    "parcels",
    "parcel_adjustments",
    "sales_archive",
    "sales_closed",
    "service_orders",
    "order_status_history",
    "os_arquivadas",
    "estoque_capas",
    "estoque_peliculas",
    "compatibilidade_peliculas",
    "estoque_pecas",
]


def conectar_somente_leitura(path: Path):
    return sqlite3.connect(
        f"file:{path.as_posix()}?mode=ro",
        uri=True
    )


def tabela_existe(conexao, tabela: str):
    resultado = conexao.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (tabela,)
    ).fetchone()

    return resultado is not None


def obter_colunas(conexao, tabela: str):
    return [
        linha[1]
        for linha in conexao.execute(
            f'PRAGMA table_info("{tabela}")'
        ).fetchall()
    ]


def contar_registros(conexao, tabela: str):
    return conexao.execute(
        f'SELECT COUNT(*) FROM "{tabela}"'
    ).fetchone()[0]


def validar_banco(conexao, nome: str):
    integridade = conexao.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    if integridade != "ok":
        raise RuntimeError(
            f"O banco {nome} falhou na verificação de integridade: "
            f"{integridade}"
        )

    erros_fk = conexao.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if erros_fk:
        raise RuntimeError(
            f"O banco {nome} possui chaves estrangeiras inválidas: "
            f"{erros_fk}"
        )


def validar_estruturas(con_antigo, con_novo):
    for tabela in TABELAS_MIGRACAO:
        if not tabela_existe(con_antigo, tabela):
            raise RuntimeError(
                f"A tabela '{tabela}' não existe no banco antigo."
            )

        if not tabela_existe(con_novo, tabela):
            raise RuntimeError(
                f"A tabela '{tabela}' não existe no banco novo."
            )

        colunas_antigas = obter_colunas(con_antigo, tabela)
        colunas_novas = obter_colunas(con_novo, tabela)

        if colunas_antigas != colunas_novas:
            raise RuntimeError(
                f"Estrutura diferente na tabela '{tabela}'.\n"
                f"Banco antigo: {colunas_antigas}\n"
                f"Banco novo:   {colunas_novas}"
            )


def validar_destino_vazio(con_novo):
    tabelas_preenchidas = []

    for tabela in TABELAS_MIGRACAO:
        quantidade = contar_registros(con_novo, tabela)

        if quantidade:
            tabelas_preenchidas.append(
                f"{tabela}: {quantidade}"
            )

    if tabelas_preenchidas:
        detalhes = "\n".join(tabelas_preenchidas)

        raise RuntimeError(
            "A migração foi cancelada porque o banco novo já possui "
            "dados nas tabelas que seriam migradas:\n"
            f"{detalhes}"
        )


def criar_backup_banco_novo():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_path = DB_NOVO.parent / (
        f"bestsystem_backup_antes_migracao_{timestamp}.db"
    )

    with sqlite3.connect(DB_NOVO) as origem:
        with sqlite3.connect(backup_path) as destino:
            origem.backup(destino)

    return backup_path


def copiar_tabela(con_antigo, con_novo, tabela: str):
    colunas = obter_colunas(con_antigo, tabela)

    colunas_sql = ", ".join(
        f'"{coluna}"'
        for coluna in colunas
    )

    placeholders = ", ".join(
        "?"
        for _ in colunas
    )

    registros = con_antigo.execute(
        f'SELECT {colunas_sql} FROM "{tabela}"'
    ).fetchall()

    if registros:
        con_novo.executemany(
            f"""
            INSERT INTO "{tabela}" ({colunas_sql})
            VALUES ({placeholders})
            """,
            registros
        )

    return len(registros)


def migrar_dados():
    con_antigo = conectar_somente_leitura(DB_ANTIGO)
    con_novo = sqlite3.connect(DB_NOVO)

    con_antigo.execute("PRAGMA query_only = ON")
    con_novo.execute("PRAGMA foreign_keys = ON")

    quantidades_origem = {}

    try:
        print("\nVerificando os bancos de dados...")

        validar_banco(con_antigo, "antigo")
        validar_banco(con_novo, "novo")
        validar_estruturas(con_antigo, con_novo)
        validar_destino_vazio(con_novo)

        print("Estruturas e integridade verificadas.")

        con_novo.execute("BEGIN IMMEDIATE")

        for tabela in TABELAS_MIGRACAO:
            quantidade = copiar_tabela(
                con_antigo,
                con_novo,
                tabela
            )

            quantidades_origem[tabela] = quantidade

            print(
                f"{tabela}: {quantidade} registro(s) migrado(s)"
            )

        erros_fk = con_novo.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if erros_fk:
            raise RuntimeError(
                "A migração produziu chaves estrangeiras inválidas: "
                f"{erros_fk}"
            )

        for tabela, quantidade_origem in quantidades_origem.items():
            quantidade_destino = contar_registros(
                con_novo,
                tabela
            )

            if quantidade_destino != quantidade_origem:
                raise RuntimeError(
                    f"Contagem divergente em '{tabela}': "
                    f"origem={quantidade_origem}, "
                    f"destino={quantidade_destino}"
                )

        con_novo.commit()

        print("\nMigração concluída e validada com sucesso.")

    except Exception:
        con_novo.rollback()
        print("\nErro encontrado. Todas as inserções foram desfeitas.")
        raise

    finally:
        con_antigo.close()
        con_novo.close()


def main():
    if not DB_ANTIGO.exists():
        raise FileNotFoundError(
            f"Banco em uso não encontrado:\n{DB_ANTIGO}"
        )

    if not DB_NOVO.exists():
        raise FileNotFoundError(
            f"Banco novo não encontrado:\n{DB_NOVO}"
        )

    if DB_ANTIGO.resolve() == DB_NOVO.resolve():
        raise RuntimeError(
            "O banco antigo e o banco novo apontam para o mesmo arquivo."
        )

    print("BANCO DE ORIGEM:")
    print(DB_ANTIGO)

    print("\nBANCO DE DESTINO:")
    print(DB_NOVO)

    print(
        "\nFeche as duas aplicações Streamlit antes de continuar."
    )

    confirmacao = input(
        '\nDigite MIGRAR para iniciar: '
    ).strip()

    if confirmacao != "MIGRAR":
        print("Migração cancelada.")
        return

    backup_path = criar_backup_banco_novo()

    print(f"\nBackup criado em:\n{backup_path}\n")

    migrar_dados()


if __name__ == "__main__":
    main()