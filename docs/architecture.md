# Architecture

## System Overview

The fal-bundles system is a content-addressable storage solution for managing resource bundles. It consists of two main components:

1. **API Server** - FastAPI-based REST API for blob and bundle management
2. **CLI** - Python command-line interface for creating, listing, and downloading bundles

The system uses content-addressable storage (hash-based deduplication) to efficiently store files and enable idempotent uploads.

See [docs/project_overview.md](./project_overview.md) for more details.

## Core Concepts

- **Blob** - a content-addressed file stored by its SHA-256 hash. Blobs are immutable and deduplicated - the same file content is only stored once regardless of how many bundles reference it.
- **Bundle** - a collection of blobs with associated relative file paths. Bundles are represented by JSON manifests that map paths to blob hashes.
  - **Summary** - a JSON file that contains all bundle metadata except the file list
  - **Manifest** - a JSON file that contains all bundle metadata and the file list
- **Deduplication** - files are identified by their SHA-256 hash. Multiple bundles can reference the same blob without duplicating storage.

## Project Structure

See [docs/project_structure.md](./project_structure.md)

## API Design

See [docs/api/README.md](./api/README.md)

## Storage Implementation

See [docs/storage/README.md](./storage/README.md)

## CLI Design

See [docs/cli/README.md](./cli/README.md)

## Data Flow

```
CLI                    API Server              Storage
 |                         |                       |
 |--1. Discover files----> |                       |
 |                         |                       |
 |--2. POST /preflight---->|                       |
 |                         |--Check blob exists--->|
 |<---Missing hashes-------|                       |
 |                         |                       |
 |--3. PUT /blobs/{h}----->|                       |
 |   (for each missing)    |--Verify & store------>|
 |<---201 Created----------|                       |
 |                         |                       |
 |--4. POST /bundles------>|                       |
 |                         |--Verify blobs-------->|
 |                         |--Write manifest------>|
 |                         |--Write summary------->|
 |<---Bundle ID------------|                       |
 |                         |                       |
 |--5. Print ID            |                       |
```

### Download Bundle Flow

```
CLI                    API Server              Storage
 |                         |                       |
 |--1. GET /bundles/{id}-->|                       |
 |      /download          |--Read manifest------->|
 |                         |--Collect blobs------->|
 |                         |--Stream ZIP---------->|
 |<---Streaming ZIP--------|                       |
 |                         |                       |
 |--2. Write to file       |                       |
 |--3. Print success       |                       |
```