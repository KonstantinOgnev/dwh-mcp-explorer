from dwh_mcp.databricks_provider import (
    DatabricksMetadataProvider,
)
from dwh_mcp.databricks_lineage_provider import (
    DatabricksLineageProvider,
)
from dwh_mcp.databricks_knowledge import (
    investigate_databricks_object,
)


def main():
    full_name = "marketplace_lab.gold.fact_orders"

    metadata_provider = DatabricksMetadataProvider()
    lineage_provider = DatabricksLineageProvider()

    result = investigate_databricks_object(
        full_name=full_name,
        metadata_provider=metadata_provider,
        lineage_provider=lineage_provider,
    )

    assert result["status"] == "completed"
    assert result["object_name"] == full_name

    metadata = result["metadata"]
    assert metadata["full_name"] == full_name

    table_lineage = result["table_lineage"]
    column_lineage = result["column_lineage"]

    assert table_lineage["status"] == "completed"
    assert column_lineage["status"] == "completed"

    assert isinstance(table_lineage["events"], list)
    assert isinstance(column_lineage["events"], list)

    print("OBJECT:", result["object_name"])
    print("TABLE TYPE:", metadata["table_type"])
    print("DATA FORMAT:", metadata["data_source_format"])
    print("TABLE LINEAGE EVENTS:", table_lineage["row_count"])
    print("COLUMN LINEAGE EVENTS:", column_lineage["row_count"])
    print("STAGE 6.6.3: PASSED")


if __name__ == "__main__":
    main()