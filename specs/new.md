# diff / sync

sync this bundle to this directory

### input
- directory you want to sync 
- bundle id 

### implementation details
- walk dir -> figure out paths of current files
- api endpoint
  - receive list of paths + file hashes (which represents file content)
  - send back
    - zip w/ files
    - `to_cleanup`: list of paths to delete
- cli - receive zip -> unzip + replace any files

### output
- dir that you pass has same structure as bundle



bunde id (tests folder): `01K8KRBHVJC3R9JTD8ZHDAJF3T`



bundle manifest
```json
{
  "id": "01K8KAGE82ZJ4D32D4PYVNB00H",
  "created_at": "2025-10-27T17:12:30.210203Z",
  "hash_algo": "sha256",
  "files": [
    {
      "bundle_path": "file1.txt",
      "size_bytes": 100,
      "hash": "2816597888e4a0d3a36b82b83316ab32680eb8f00f8cd3b904d681246d285a0e",
      "hash_algo": "sha256"
    },
    {
      "bundle_path": "file2.txt",
      "size_bytes": 250,
      "hash": "4b6864de8563969279cb13b1bcbab4541ba7c42b72f007ae0a503d891eb4ae33",
      "hash_algo": "sha256"
    },
    {
      "bundle_path": "file3.txt",
      "size_bytes": 50,
      "hash": "5de6bf7f73e34ca05016906d50a4f3ced729bffd9fd1beefb0e0c6a0b5c136e4",
      "hash_algo": "sha256"
    }
  ],
  "file_count": 3,
  "total_bytes": 400,
  "merkle_root": "185559629fe40631a0db4e7d0fdeb1d13e436d3999a2e96513e5ba69c21cbfea"
}
```