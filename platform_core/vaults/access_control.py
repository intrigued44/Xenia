from platform_core.vaults.models import VaultLevel

VAULT_ACCESS_RULES = {
    "employee":   [VaultLevel.PERSONAL],
    "team_lead":  [VaultLevel.PERSONAL, 
                   VaultLevel.ROLE, 
                   VaultLevel.TEAM],
    "manager":    [VaultLevel.ROLE, 
                   VaultLevel.TEAM],
    "executive":  [VaultLevel.TEAM, 
                   VaultLevel.ORGANIZATION],
    "admin":      [VaultLevel.ORGANIZATION]
}

AGENT_ACCESS_RULES = {
    "scout":      [VaultLevel.ORGANIZATION],
    "operator":   [VaultLevel.TEAM],
    "closer":     [VaultLevel.PERSONAL],
    "architect":  [VaultLevel.ROLE, VaultLevel.TEAM],
    "workflow":   [VaultLevel.PERSONAL, VaultLevel.ROLE],
    "knowledge":  [VaultLevel.PERSONAL, VaultLevel.ROLE,
                   VaultLevel.TEAM, VaultLevel.ORGANIZATION],
    "strategist": [VaultLevel.ORGANIZATION]
}

class VaultAccessError(Exception):
    pass

def check_access(role: str, 
                 vault_level: VaultLevel) -> None:
    allowed = VAULT_ACCESS_RULES.get(role, [])
    if vault_level not in allowed:
        raise VaultAccessError(
            f"Role '{role}' cannot access "
            f"'{vault_level}' vault"
        )

def check_agent_access(agent_name: str,
                       vault_level: VaultLevel) -> None:
    allowed = AGENT_ACCESS_RULES.get(agent_name, [])
    if vault_level not in allowed:
        raise VaultAccessError(
            f"Agent '{agent_name}' cannot access "
            f"'{vault_level}' vault"
        )
