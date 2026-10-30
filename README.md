# Task 1: Source Normalisation and Filtering

A standalone, deterministic Python pipeline for processing raw source records, validating their structure, identifying and deduplicating overlapping sources while preserving discovery lineage, and enforcing strict competitor and source policies.

---

## Table of Contents

- [Overview](#overview)
- [Architecture and Implementation Workflow](#architecture-and-implementation-workflow)
  - [1. Parse and Validate](#1-parse-and-validate)
  - [2. Normalise and Deduplicate](#2-normalise-and-deduplicate)
  - [3. Apply Policies](#3-apply-policies)
  - [4. Export Results](#4-export-results)
  - [Optional Extension: Safe Live Connector](#optional-extension-safe-live-connector)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
- [Running the Pipeline](#running-the-pipeline)
- [Running Tests](#running-tests)
- [Fixtures and Assumptions](#fixtures-and-assumptions)
- [Acceptance Criteria](#acceptance-criteria)
- [Engineering Trade-offs and Design Decisions](#engineering-trade-offs-and-design-decisions)

---

## Overview

**Selected Task: Task 1 — Source Normalisation and Filtering**

This repository implements a modular, pipeline-driven application designed to transform raw source records into validated, normalized, deduplicated, and policy-classified data.

The primary objectives are:

- Validate incoming records against strict data schemas.
- Normalize URLs into canonical formats.
- Identify and merge duplicate sources.
- Preserve source provenance and discovery lineage.
- Apply deterministic competitor and source eligibility policies.
- Export both accepted and rejected records with explicit classification reasons.

The implementation prioritizes **determinism, transparency, security, and testability**.

---

## Architecture and Implementation Workflow

The application is implemented in Python using a modular architecture consisting of four main processing phases.

### 1. Parse and Validate (`models.py`)

Uses **Pydantic** to enforce strict schema contracts.

- Incoming JSON records are parsed into `InputRecord` objects.
- Required fields and data types are validated.
- Malformed records raise a `ValidationError`.
- Invalid records are predictably discarded rather than silently propagated downstream.

### 2. Normalise and Deduplicate (`normaliser.py`)

Standardizes URLs and identifies duplicate source records.

The normalization process extracts:

- URL scheme.
- Network location (domain).
- URL path.

Query parameters and fragments are intentionally removed to eliminate tracking information and generate a canonical URL.

For example:

```text
https://example.com/article?id=123&utm_source=news#section
```

Becomes:

```text
https://example.com/article
```

When multiple records resolve to the same canonical URL:

- Duplicate records are grouped together.
- Their provenance arrays are combined.
- A unified `discovery_lineage` is generated.
- Original discovery information is preserved to prevent data loss.

### 3. Apply Policies (`policy.py`)

Implements a configurable, deterministic rules engine that evaluates the `source_type` of each normalized record.

Each record receives an explicit eligibility classification:

| Eligibility Status | Description |
|---|---|
| `ELIGIBLE` | The source satisfies the defined acceptance policies. |
| `EXCLUDED` | The source violates an exclusion policy. |
| `VERIFICATION_REQUIRED` | The source requires further verification before being trusted. |

Additionally, the engine appends specific `reason_codes` explaining why each classification was assigned.

### 4. Export Results (`main.py`)

The final pipeline stage exports both accepted and rejected records into a structured output format.

This ensures that downstream systems can:

- Access validated and normalized records.
- Identify excluded sources.
- Inspect eligibility classifications.
- Understand the reasoning behind each policy decision.
- Review preserved discovery lineage.

### Optional Extension: Safe Live Connector (`connector.py`)

The repository also includes a `SafeLiveConnector`, demonstrating secure external data fetching.

The connector incorporates several security measures:

- **SSRF Protection:** Resolves hostnames and blocks private and loopback IP addresses.
- **Response Size Limits:** Enforces strict byte-size restrictions to prevent memory exhaustion.
- **Connection Timeouts:** Prevents indefinite waiting for external requests.
- **Redirect Restrictions:** Limits the number of permitted HTTP redirects.
- **Content-Type Validation:** Ensures that incoming responses match the expected content types.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or higher |
| Pydantic | As specified in `requirements.txt` |
| Pytest | As specified in `requirements.txt` |

No external services or undisclosed credentials are required to run the application.

---

## Installation and Setup

Navigate to the root directory of the project:

```bash
cd src/task-1_georgios-boukouvalas/
```

### 1. Create a Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate the Virtual Environment

**Windows:**

```bash
.\.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Pipeline

To execute the complete end-to-end pipeline demonstration, run:

```bash
python main.py
```

The execution performs the following operations:

1. Loads and parses the input fixture.
2. Validates incoming records.
3. Normalizes source URLs.
4. Identifies and merges duplicate records.
5. Applies source eligibility policies.
6. Executes the live connector security tests.
7. Displays step-by-step processing information in the terminal.
8. Exports the final processed data.

**Output location:**

```text
examples/output.json
```

---

## Running Tests

Automated tests are implemented using **Pytest**.

The test suite programmatically validates edge cases, failure states, and compliance with the core business logic.

To execute all tests, ensure that the virtual environment is activated and run:

```bash
pytest tests/
```

---

## Fixtures and Assumptions

### Input Fixture (`fixtures/input.json`)

The project includes a handcrafted local JSON fixture containing exactly six records, specifically designed to satisfy the task's edge-case requirements.

| Record | Description |
|---|---|
| 1 | Valid primary source. |
| 2 | Exact canonical duplicate of the primary source. |
| 3 | Competitor product claim. |
| 4 | Competitor generic claim. |
| 5 | Record with a null publication date. |
| 6 | Structurally malformed record. |

### Assumptions

- **Localized Processing:** Processing is performed locally. Downstream persistence mechanisms, such as database insertion, are outside the scope of this normalization component.
- **Canonical URL Definition:** Canonical URLs are determined strictly by domain and path. Query parameters are assumed to be non-routing elements, such as UTM tracking parameters.
- **Deterministic Processing:** No generative AI or probabilistic models are used for policy application. All classifications are based on explicit, predefined rules.

---

## Acceptance Criteria

The implementation satisfies the task requirements through the following mechanisms:

### Validation

Pydantic ensures that incoming records adhere to the defined data types and required fields.

Malformed records trigger validation errors and are handled without compromising downstream processing.

### Deduplication and Provenance

The `normaliser.py` module groups records using their canonical URLs.

When duplicates are identified, their provenance arrays are iterated over and merged into a unified `discovery_lineage`, preserving the original discovery information.

### Unknown Publication Dates

Pydantic's `Optional[str]` allows null publication dates to pass through the system as Python `None`.

No timestamps are inferred, generated, or fabricated when publication dates are unavailable.

### Policy Application

The `policy.py` engine successfully distinguishes standard sources from competitor claims.

- Competitor product claims are explicitly classified as `EXCLUDED`.
- Generic competitor claims are classified as `VERIFICATION_REQUIRED`, identifying them as discovery leads rather than trusted evidence.
- Standard sources are evaluated according to the configured eligibility rules.

### Explicit Rejections

Excluded records are preserved in the final output file (`examples/output.json`).

Each rejected record includes an explicit and inspectable `reason_codes` array explaining the classification decision.

---

## Engineering Trade-offs and Design Decisions

### 1. In-Memory Deduplication vs. Database Constraints

Deduplication is implemented in memory using Python dictionaries.

This approach was selected because the project requires a small, reliable, and easily testable component.

Although production systems processing millions of records might benefit from database constraints or distributed processing frameworks such as Apache Spark, in-memory processing minimizes infrastructure overhead and satisfies the current architectural requirements.

### 2. Pydantic vs. Custom Validation Logic

Pydantic was selected over standard Python `dataclasses` and manually implemented JSON validation.

**Trade-off:** Introducing a third-party dependency.

**Benefits:**

- Structured and localized validation errors through `ValidationError`.
- Automatic type validation and coercion according to the defined schema.
- Strict schema enforcement.
- Convenient serialization capabilities.
- Reduced custom validation code.

### 3. Deterministic Policies vs. Machine Learning Classification

The policy engine uses predefined deterministic rules based on source type schemas rather than machine learning classification.

This design ensures:

- Predictable and repeatable test execution.
- Transparent eligibility decisions.
- Explicit and inspectable `reason_codes`.
- No dependency on probabilistic model outputs.
- No black-box classification behavior.

The result is a transparent and maintainable filtering mechanism where every decision can be traced back to a predefined rule.

---

## Final Notes

This implementation provides a deterministic and modular foundation for source normalization and filtering.

By combining schema validation, canonical URL processing, provenance preservation, explicit eligibility policies, and secure external data fetching, the pipeline ensures that source records are processed consistently and that every classification decision remains inspectable.

The architecture is intentionally lightweight, testable, and extensible, allowing additional source types, normalization rules, and eligibility policies to be introduced without significantly changing the core pipeline.
