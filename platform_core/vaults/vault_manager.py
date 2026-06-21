import hashlib, json, uuid, time
from platform_core.vaults.models import (
    VaultLevel, VaultRecord, ContributionRequest
)
from platform_core.vaults.access_control import (
    check_access, check_agent_access, VaultAccessError
)
from client.db import get_connection, dict_factory

class VaultManager:

    def store(self, record: VaultRecord,
              requesting_role: str = "employee") -> str:
        check_access(requesting_role, record.vault_level)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO vault_records
            (id, vault_level, tenant_id, contributor_hash,
             record_type, content, metadata, created_at,
             approved_by, approved_at, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            record.id,
            record.vault_level.value,
            record.tenant_id,
            record.contributor_hash,
            record.record_type,
            json.dumps(record.content),
            json.dumps(record.metadata),
            record.created_at or int(time.time()),
            record.approved_by,
            record.approved_at,
            record.status
        ))
        conn.commit()
        conn.close()
        return record.id

    def store_as_agent(self, record: VaultRecord,
                       agent_name: str) -> str:
        check_agent_access(agent_name, record.vault_level)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO vault_records
            (id, vault_level, tenant_id, contributor_hash,
             record_type, content, metadata, created_at,
             approved_by, approved_at, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            record.id,
            record.vault_level.value,
            record.tenant_id,
            record.contributor_hash,
            record.record_type,
            json.dumps(record.content),
            json.dumps(record.metadata),
            record.created_at or int(time.time()),
            record.approved_by,
            record.approved_at,
            record.status
        ))
        conn.commit()
        conn.close()
        return record.id

    def retrieve(self, vault_level: VaultLevel,
                 tenant_id: str,
                 record_type: str = None,
                 requesting_role: str = "employee",
                 limit: int = 100) -> list:
        check_access(requesting_role, vault_level)
        conn = get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        if record_type:
            rows = cursor.execute("""
                SELECT * FROM vault_records
                WHERE vault_level=? AND tenant_id=?
                AND record_type=? AND status='approved'
                ORDER BY created_at DESC LIMIT ?
            """, (vault_level.value, tenant_id,
                  record_type, limit)).fetchall()
        else:
            rows = cursor.execute("""
                SELECT * FROM vault_records
                WHERE vault_level=? AND tenant_id=?
                AND status='approved'
                ORDER BY created_at DESC LIMIT ?
            """, (vault_level.value, tenant_id,
                  limit)).fetchall()

        conn.close()

        for row in rows:
            if row.get("content"):
                try:
                    row["content"] = json.loads(
                        row["content"]
                    )
                except Exception as e:
                    import logging
                    logging.error(f"context: {e}", exc_info=True)
            if row.get("metadata"):
                try:
                    row["metadata"] = json.loads(
                        row["metadata"]
                    )
                except Exception as e:
                    import logging
                    logging.error(f"context: {e}", exc_info=True)
        return rows

    def retrieve_as_agent(self, vault_level: VaultLevel,
                          tenant_id: str,
                          agent_name: str,
                          record_type: str = None) -> list:
        check_agent_access(agent_name, vault_level)
        conn = get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        if record_type:
            rows = cursor.execute("""
                SELECT * FROM vault_records
                WHERE vault_level=? AND tenant_id=?
                AND record_type=? AND status='approved'
                ORDER BY created_at DESC LIMIT 100
            """, (vault_level.value, tenant_id,
                  record_type)).fetchall()
        else:
            rows = cursor.execute("""
                SELECT * FROM vault_records
                WHERE vault_level=? AND tenant_id=?
                AND status='approved'
                ORDER BY created_at DESC LIMIT 100
            """, (vault_level.value,
                  tenant_id)).fetchall()

        conn.close()
        for row in rows:
            if row.get("content"):
                try:
                    row["content"] = json.loads(
                        row["content"]
                    )
                except Exception as e:
                    import logging
                    logging.error(f"context: {e}", exc_info=True)
        return rows

    def request_contribution(self,
                             record_id: str,
                             from_vault: VaultLevel,
                             to_vault: VaultLevel,
                             summary: str,
                             tenant_id: str,
                             contributor_hash: str) -> str:
        request = ContributionRequest(
            id=str(uuid.uuid4()),
            from_vault=from_vault,
            to_vault=to_vault,
            record_id=record_id,
            contributor_hash=contributor_hash,
            summary=summary,
            tenant_id=tenant_id,
            created_at=int(time.time())
        )
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contribution_requests
            (id, from_vault, to_vault, record_id,
             contributor_hash, summary, tenant_id,
             created_at, status)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            request.id,
            request.from_vault.value,
            request.to_vault.value,
            request.record_id,
            request.contributor_hash,
            request.summary,
            request.tenant_id,
            request.created_at,
            request.status
        ))
        conn.commit()
        conn.close()
        return request.id

    def approve_contribution(self, request_id: str,
                             approved_by: str = "employee") -> bool:
        conn = get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        request = cursor.execute(
            "SELECT * FROM contribution_requests "
            "WHERE id=?", (request_id,)
        ).fetchone()

        if not request or request["status"] != "pending":
            conn.close()
            return False

        # Load original record
        original = cursor.execute(
            "SELECT * FROM vault_records WHERE id=?",
            (request["record_id"],)
        ).fetchone()

        if not original:
            conn.close()
            return False

        # Anonymize: re-hash contributor identity
        original_hash = original.get(
            "contributor_hash", ""
        )
        anonymous_hash = hashlib.sha256(
            (original_hash + "salt_nous").encode()
        ).hexdigest()[:16]

        # Parse and strip personal identifiers from content
        content = original.get("content", "{}")
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except Exception:
                content = {}

        # Remove any personal identifier fields
        for key in ["user_id", "employee_id",
                    "name", "email", "device_id"]:
            content.pop(key, None)

        # Store promoted record in target vault
        promoted_id = str(uuid.uuid4())
        now = int(time.time())
        cursor.execute("""
            INSERT INTO vault_records
            (id, vault_level, tenant_id, contributor_hash,
             record_type, content, metadata, created_at,
             approved_by, approved_at, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            promoted_id,
            request["to_vault"],
            request["tenant_id"],
            anonymous_hash,
            original.get("record_type", "workflow"),
            json.dumps(content),
            original.get("metadata", "{}"),
            now,
            approved_by,
            now,
            "approved"
        ))

        # Update request status
        cursor.execute("""
            UPDATE contribution_requests
            SET status='approved', resolved_at=?
            WHERE id=?
        """, (now, request_id))

        conn.commit()
        conn.close()
        return True

    def reject_contribution(self,
                            request_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contribution_requests
            SET status='rejected', resolved_at=?
            WHERE id=?
        """, (int(time.time()), request_id))
        conn.commit()
        conn.close()
        return True

    def get_pending_contributions(self,
                                  tenant_id: str) -> list:
        conn = get_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT * FROM contribution_requests
            WHERE tenant_id=? AND status='pending'
            ORDER BY created_at DESC
        """, (tenant_id,)).fetchall()
        conn.close()
        return rows

    def get_vault_summary(self, tenant_id: str) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        summary = {}
        for level in VaultLevel:
            count = cursor.execute("""
                SELECT COUNT(*) FROM vault_records
                WHERE vault_level=? AND tenant_id=?
                AND status='approved'
            """, (level.value, tenant_id)).fetchone()
            summary[level.value] = count[0] if count else 0
        pending = cursor.execute("""
            SELECT COUNT(*) FROM contribution_requests
            WHERE tenant_id=? AND status='pending'
        """, (tenant_id,)).fetchone()
        summary["pending_contributions"] = pending[0] if pending else 0
        conn.close()
        return summary
