
from databricks.sdk import WorkspaceClient


class DatabricksMetadataProvider:
    """Read-only access to Unity Catalog metadata."""

    def __init__(self, profile: str = "MARKETPLACE_LAB"):
        self.client = WorkspaceClient(profile=profile)

    def list_catalogs(self) -> list[str]:
        return [
            catalog.name
            for catalog in self.client.catalogs.list()
        ]

    def list_schemas(self, catalog_name: str) -> list[str]:
        return [
            schema.name
            for schema in self.client.schemas.list(
                catalog_name=catalog_name
            )
        ]

    def list_tables(
        self,
        catalog_name: str,
        schema_name: str
    ) -> list[str]:
        return [
            table.name
            for table in self.client.tables.list(
                catalog_name=catalog_name,
                schema_name=schema_name
            )
        ]

    def describe_table(
        self,
        full_name: str
    ) -> dict:
        table = self.client.tables.get(
            full_name=full_name
        )

        return {
            "full_name": table.full_name,
            "table_type": table.table_type.value if table.table_type else None,
            "data_source_format": (
                table.data_source_format.value
                if table.data_source_format else None
            ),
            "comment": table.comment,
            "columns": [
                {
                    "name": col.name,
                    "type": col.type_text,
                    "nullable": col.nullable,
                    "position": col.position
                }
                for col in (table.columns or [])
            ],
            "properties": table.properties or {}
        }
