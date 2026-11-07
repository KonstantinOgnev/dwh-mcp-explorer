# DWH MCP Explorer — Technical Documentation

This directory contains the technical documentation for the DWH MCP Explorer project, a Python-based Model Context Protocol (MCP) server integrating PostgreSQL and Azure Databricks.

Documentation is available in English (EN) and Russian (RU).

## Documentation Index

### 1. Solution Architecture

High-level architecture, MCP components, platform integrations, and data flows.

- [Solution Architecture — English](architecture/DWH_MCP_Explorer_Architecture_EN.pdf)
- [Solution Architecture — Russian](architecture/DWH_MCP_Explorer_Architecture_RU.pdf)

### 2. Technical Implementation Guide

Implementation details, Python modules, MCP tools, metadata providers, and integration design.

- [Technical Implementation Guide — English](implementation/DWH_MCP_Explorer_Technical_Guide_EN.pdf)
- [Technical Implementation Guide — Russian](implementation/DWH_MCP_Explorer_Technical_Guide_RU.pdf)

### 3. Deployment and Configuration Guide

Environment preparation, dependencies, credentials, PostgreSQL and Databricks connectivity, and Claude Desktop configuration.

- [Deployment and Configuration — English](deployment/DWH_MCP_Explorer_Deployment_Configuration_EN.pdf)
- [Deployment and Configuration — Russian](deployment/DWH_MCP_Explorer_Deployment_Configuration_RU.pdf)

### 4. Testing and Validation Guide

Test coverage, MCP integration testing, positive and negative scenarios, and validation results.

- [Testing and Validation — English](testing/DWH_MCP_Explorer_Testing_Validation_EN.pdf)
- [Testing and Validation — Russian](testing/DWH_MCP_Explorer_Testing_Validation_RU.pdf)

## Architecture Overview

```text
Claude Desktop
      |
      v
  MCP Server
      |
      +-- PostgreSQL Metadata
      |      +-- Schemas and Tables
      |      +-- Primary / Foreign Keys
      |      +-- SQL Repository
      |      +-- Reconciliation
      |
      +-- Azure Databricks
             +-- Unity Catalog
             +-- Table Metadata
             +-- Table / Column Lineage
             +-- Knowledge Object
             +-- Grain Validation
```

## Recommended Reading Order

1. Solution Architecture
2. Technical Implementation Guide
3. Deployment and Configuration Guide
4. Testing and Validation Guide

## Related Resources

- [Main Project README](../README.md)
- [Python MCP Server](../server.py)
- [MCP Python Modules](../dwh_mcp/)
- [Automated Tests](../tests/)

---

**DWH MCP Explorer** — Data Engineering · Data Architecture · Python · MCP · PostgreSQL · Azure Databricks · AI Integration
