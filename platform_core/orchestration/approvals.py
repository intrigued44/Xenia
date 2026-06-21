import time
import sqlite3
from client.db import get_connection

class ApprovalManager:
    def __init__(self, engine):
        self.engine = engine

    def get_pending(self, tenant_id: str) -> list:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, plan_id, step_id, tool_name, params_summary, created_at 
            FROM pending_approvals 
            WHERE status = 'pending' AND tenant_id = ?
        ''', (tenant_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def approve(self, approval_id: str, tenant_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pending_approvals 
            SET status = 'approved', resolved_at = ? 
            WHERE id = ? AND tenant_id = ?
        ''', (int(time.time()), approval_id, tenant_id))
        
        cursor.execute('SELECT plan_id FROM pending_approvals WHERE id = ?', (approval_id,))
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        
        if row:
            plan_id = row[0]
            self.engine.resume(plan_id, approval_id, tenant_id)
            return True
        return False

    def reject(self, approval_id: str, reason: str, tenant_id: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pending_approvals 
            SET status = 'rejected', resolved_at = ? 
            WHERE id = ? AND tenant_id = ?
        ''', (int(time.time()), approval_id, tenant_id))
        
        cursor.execute('SELECT plan_id FROM pending_approvals WHERE id = ?', (approval_id,))
        row = cursor.fetchone()
        
        if row:
            plan_id = row[0]
            cursor.execute('UPDATE plans SET status = "failed" WHERE id = ?', (plan_id,))
            
        conn.commit()
        conn.close()
        return True

    def expire_old(self, hours: int = 24) -> int:
        threshold = int(time.time()) - (hours * 3600)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE pending_approvals 
            SET status = 'expired' 
            WHERE status = 'pending' AND created_at < ?
        ''', (threshold,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count
