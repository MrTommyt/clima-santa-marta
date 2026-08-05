from __future__ import annotations

import gzip
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO

from minio import Minio
from minio.error import S3Error


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    checksum_sha256: str
    size_bytes: int


class MinioBronzeStore:
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def exists(self, object_key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_key)
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                return False
            raise

    def put_json(self, object_key: str, payload: bytes) -> StoredObject:
        compressed = gzip.compress(payload)
        checksum = sha256(compressed).hexdigest()

        self.client.put_object(
            bucket_name=self.bucket,
            object_name=object_key,
            data=BytesIO(compressed),
            length=len(compressed),
            content_type="application/gzip",
            metadata={
                "checksum-sha256": checksum,
            },
        )

        return StoredObject(
            object_key=object_key,
            checksum_sha256=checksum,
            size_bytes=len(compressed),
        )
