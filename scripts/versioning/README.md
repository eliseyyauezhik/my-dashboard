# Snapshot / Restore

Stable versioning helpers for local projects.

## Create snapshot

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\versioning\snapshot.ps1 -ProjectPath "c:\path\to\project" -Label "before_hero_update"
```

Output:

`SNAPSHOT_CREATED=...zip`

## Restore latest snapshot

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\versioning\restore.ps1 -ProjectPath "c:\path\to\project" -ConfirmRestore
```

## Restore specific snapshot

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\versioning\restore.ps1 -ProjectPath "c:\path\to\project" -ArchivePath "c:\path\to\project\.snapshots\snapshot_20260307_120000_before_hero.zip" -ConfirmRestore
```

Notes:

- `restore.ps1` creates an automatic `pre_restore` snapshot before rollback.
- `.snapshots`, `.git`, `node_modules`, and `__pycache__` are excluded from snapshots.
