from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import yaml


@dataclass(frozen=True)
class S3Source:
    name: str
    environment: str
    account_id: str
    bucket: str
    prefix: str


def load_sources(config_path: Path) -> tuple[dict[str, Any], list[S3Source]]:
    with config_path.open("r", encoding="utf-8") as fh:
        payload = yaml.safe_load(fh) or {}

    defaults = payload.get("defaults", {})
    sources_raw = payload.get("sources", [])
    sources = [S3Source(**item) for item in sources_raw]
    return defaults, sources


def iter_s3_objects(client: Any, bucket: str, prefix: str) -> list[dict[str, Any]]:
    paginator = client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    objects: list[dict[str, Any]] = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            objects.append(obj)
    return objects


def download_source(source: S3Source, client: Any, download_root: Path) -> list[dict[str, Any]]:
    objects = iter_s3_objects(client, source.bucket, source.prefix)
    source_root = download_root / source.environment / source.name
    source_root.mkdir(parents=True, exist_ok=True)

    downloaded: list[dict[str, Any]] = []
    for obj in objects:
        key = obj["Key"]
        relative = key[len(source.prefix) :] if key.startswith(source.prefix) else key
        destination = source_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(source.bucket, key, str(destination))

        downloaded.append(
            {
                "source": source.name,
                "environment": source.environment,
                "account_id": source.account_id,
                "bucket": source.bucket,
                "key": key,
                "size": obj.get("Size"),
                "last_modified": obj.get("LastModified").isoformat()
                if obj.get("LastModified")
                else None,
                "downloaded_to": str(destination),
                "downloaded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return downloaded


def write_manifest(manifest_path: Path, rows: list[dict[str, Any]]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": len(rows),
        "files": rows,
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync raw files from S3 sources.")
    parser.add_argument(
        "--config",
        default="config/s3_sources.yaml",
        help="Path to S3 source config YAML.",
    )
    parser.add_argument(
        "--environment",
        choices=["production", "staging", "all"],
        default="all",
        help="Environment to sync.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    defaults, sources = load_sources(config_path)

    download_root = Path(defaults.get("download_root", "data/raw"))
    manifest_path = Path(defaults.get("manifest_path", "data/raw/manifest.json"))

    session = boto3.Session()
    client = session.client("s3")

    selected_sources = sources
    if args.environment != "all":
        selected_sources = [s for s in sources if s.environment == args.environment]

    all_rows: list[dict[str, Any]] = []
    for source in selected_sources:
        rows = download_source(source, client, download_root)
        all_rows.extend(rows)
        print(
            f"Synced {len(rows)} files from s3://{source.bucket}/{source.prefix} "
            f"into {download_root}/{source.environment}/{source.name}"
        )

    write_manifest(manifest_path, all_rows)
    print(f"Wrote manifest to {manifest_path} with {len(all_rows)} files.")


if __name__ == "__main__":
    main()
