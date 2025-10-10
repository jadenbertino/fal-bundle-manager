### Installation

First, install the CLI wrapper:

```bash
# Default installation to ~/.local/bin
./cli/scripts/install.sh

# Custom wrapper name
./cli/scripts/install.sh --name my-fal-bundles

# Show all options
./cli/scripts/install.sh --help
```

After installation, you can use the `fal-bundles` command from anywhere:

```bash
fal-bundles --help
fal-bundles list
fal-bundles create <path>
fal-bundles download <bundle-id>
```

### Usage

#### 1. Create
```bash
fal-bundles create <path1> [path2 ...]
```

**Flow**:
1. Discover files (recursive directory walk)
2. Hash all files (SHA-256)
3. Call preflight API to check which blobs exist
4. Upload missing blobs (with progress indication)
5. Create bundle via API
6. Prints bundle details

**Exit Codes**:
- 0: Success
- 2: Invalid/missing paths
- 3: Server reported missing blobs after upload
- 4: Network/IO errors

#### 2. List
```bash
fal-bundles list
```

**Flow**:
1. Call list bundles API
2. Format as table with columns: ID, Files, Total Size, Created, Merkle Root
3. Display to stdout

**Format**:
- Human-readable sizes (B, KB, MB, GB)
- Readable timestamps
- Aligned columns

**Exit Codes**:
- 0: Success
- 4: Network/IO errors

#### 3. Download
```bash
fal-bundles download <bundle_id>
```

**Flow**:
1. Call download bundle API
2. Stream response to local file: `bundle_{id}.{ext}`
3. Show progress during download
4. Print success message

**Exit Codes**:
- 0: Success
- 1: Unknown/unsupported format
- 2: Bundle not found (404)
- 4: Network/IO errors

### Uninstall

To uninstall the CLI wrapper:

```bash
# Default uninstall
./cli/scripts/uninstall.sh

# Custom wrapper name
./cli/scripts/uninstall.sh --name my-fal-bundles

# Show help
./cli/scripts/uninstall.sh --help
```

**Options**:
- `--name <wrapper_name>`: Name of the wrapper script to remove (default: fal-bundles)
- `--help, -h`: Show help message

**Flow**:
1. Parse command line arguments
2. Check if wrapper script exists at specified location
3. Remove wrapper script
4. Display success message

**Exit Codes**:
- 0: Success
- 1: Invalid arguments or wrapper not found
