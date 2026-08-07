"""Client mapping profile versioning — additive, tenant-scoped, non-destructive."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class MappingProfile:
    id: int
    client_id: int
    name: str
    version: int
    structural_signature: str
    mapping_json: dict[str, str]
    sheet_name: str | None
    header_row: int | None
    active: bool
    created_at: str
    created_by: str | None
    replaces_version: int | None
    status: str
    observation: str | None

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "name": self.name,
            "version": self.version,
            "structural_signature": self.structural_signature,
            "mapping": self.mapping_json,
            "sheet_name": self.sheet_name,
            "header_row": self.header_row,
            "active": self.active,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "replaces_version": self.replaces_version,
            "status": self.status,
            "observation": self.observation,
        }


class MappingProfileService:
    """CRUD over additive table `ingestion_mapping_profiles` (temp DB / future migration)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def find_active_by_signature(self, client_id: int, structural_signature: str) -> MappingProfile | None:
        cur = self.conn.execute(
            """
            SELECT id, client_id, name, version, structural_signature, mapping_json,
                   sheet_name, header_row, active, created_at, created_by,
                   replaces_version, status, observation
            FROM ingestion_mapping_profiles
            WHERE client_id = ? AND structural_signature = ? AND active = 1 AND status = 'active'
            ORDER BY version DESC LIMIT 1
            """,
            (client_id, structural_signature),
        )
        row = cur.fetchone()
        return self._row(row) if row else None

    def list_for_client(self, client_id: int) -> list[MappingProfile]:
        cur = self.conn.execute(
            """
            SELECT id, client_id, name, version, structural_signature, mapping_json,
                   sheet_name, header_row, active, created_at, created_by,
                   replaces_version, status, observation
            FROM ingestion_mapping_profiles
            WHERE client_id = ?
            ORDER BY name, version DESC
            """,
            (client_id,),
        )
        return [self._row(r) for r in cur.fetchall()]

    def create_version(
        self,
        *,
        client_id: int,
        name: str,
        structural_signature: str,
        mapping: dict[str, str],
        sheet_name: str | None,
        header_row: int | None,
        created_by: str | None,
        observation: str | None = None,
        deactivate_previous: bool = True,
    ) -> MappingProfile:
        # Never share across tenants; always new version row (no destructive UPDATE of mapping)
        cur = self.conn.execute(
            """
            SELECT COALESCE(MAX(version), 0) FROM ingestion_mapping_profiles
            WHERE client_id = ? AND name = ?
            """,
            (client_id, name),
        )
        next_ver = int(cur.fetchone()[0]) + 1
        replaces = next_ver - 1 if next_ver > 1 else None
        now = datetime.now(timezone.utc).isoformat()

        if deactivate_previous and replaces:
            self.conn.execute(
                """
                UPDATE ingestion_mapping_profiles
                SET active = 0, status = 'superseded'
                WHERE client_id = ? AND name = ? AND active = 1
                """,
                (client_id, name),
            )

        self.conn.execute(
            """
            INSERT INTO ingestion_mapping_profiles (
                client_id, name, version, structural_signature, mapping_json,
                sheet_name, header_row, active, created_at, created_by,
                replaces_version, status, observation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, 'active', ?)
            """,
            (
                client_id,
                name,
                next_ver,
                structural_signature,
                json.dumps(mapping, ensure_ascii=False),
                sheet_name,
                header_row,
                now,
                created_by,
                replaces,
                observation,
            ),
        )
        self.conn.commit()
        pid = int(self.conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        return MappingProfile(
            id=pid,
            client_id=client_id,
            name=name,
            version=next_ver,
            structural_signature=structural_signature,
            mapping_json=mapping,
            sheet_name=sheet_name,
            header_row=header_row,
            active=True,
            created_at=now,
            created_by=created_by,
            replaces_version=replaces,
            status="active",
            observation=observation,
        )

    def _row(self, row: Any) -> MappingProfile:
        return MappingProfile(
            id=row[0],
            client_id=row[1],
            name=row[2],
            version=row[3],
            structural_signature=row[4],
            mapping_json=json.loads(row[5]),
            sheet_name=row[6],
            header_row=row[7],
            active=bool(row[8]),
            created_at=row[9],
            created_by=row[10],
            replaces_version=row[11],
            status=row[12],
            observation=row[13],
        )
