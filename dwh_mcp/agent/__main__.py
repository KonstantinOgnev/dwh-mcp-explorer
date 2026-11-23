import argparse
import asyncio

from dwh_mcp.agent.runner import run_agent


def main():
    parser = argparse.ArgumentParser(
        description="Investigate a Databricks table using an AI agent."
    )
    parser.add_argument(
        "table",
        help="Full table name: catalog.schema.table",
    )
    args = parser.parse_args()

    task = (
        f"Исследуй таблицу {args.table}. "
        "Получи структуру и определи заявленный grain. "
        "Проверь уникальность и NULL для бизнес-ключа, "
        "если его можно определить по метаданным. "
        "Изучи table-level и column-level lineage. "
        "Подготовь отчёт с подтверждениями и ограничениями."
    )

    report = asyncio.run(
        run_agent(task, target_table=args.table)
    )

    print("\n========== ИТОГОВЫЙ ОТЧЁТ ==========\n")
    print(report)


if __name__ == "__main__":
    main()