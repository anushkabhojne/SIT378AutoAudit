"""
Access Control Module

Implements role-based access control (RBAC) for the Compliance Framework Engine.

Author: Senior Lead, AutoAudit
"""

from typing import List, Dict, Optional
import logging

class AccessControl:
    
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        
        #Roles mapped to permissions
        self._roles_permissions: Dict[str, List[str]] = {}
        
        #User mapped to roles
        self._user_roles: Dict[str, List[str]] = {}

    def add_role(self, role: str, permissions: List[str]):
        """
        Add a role with associated permissions.

        :param role: Role name.
        :param permissions: List of permission strings.
        """
        
        self._roles_permissions[role] = permissions
        self._logger.debug(f"Added role '{role}' with permissions {permissions}")

    def assign_role_to_user(self, user: str, role: str):
        """
        Assign a role to a user.

        :param user: User identifier.
        :param role: Role name.
        """
        
        if role not in self._roles_permissions:
            self._logger.warning(f"Role '{role}' does not exist")
            return
        
        self._user_roles.setdefault(user, [])
        
        if role not in self._user_roles[user]:
            self._user_roles[user].append(role)
            self._logger.debug(f"Assigned role '{role}' to user '{user}'")

    def remove_role_from_user(self, user: str, role: str):
        """
        Remove a role from a user.

        :param user: User identifier.
        :param role: Role name.
        """
        
        if user in self._user_roles and role in self._user_roles[user]:
            self._user_roles[user].remove(role)
            self._logger.debug(f"Removed role '{role}' from user '{user}'")

    def check_permission(self, user: str, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        :param user: User identifier.
        :param permission: Permission string.
        :return: True if user has permission, False otherwise.
        """
        
        roles = self._user_roles.get(user, [])
        
        for role in roles:
            permissions = self._roles_permissions.get(role, [])
        
            if permission in permissions:
                self._logger.debug(f"User  '{user}' has permission '{permission}' via role '{role}'")
                return True
        
        self._logger.debug(f"User  '{user}' does not have permission '{permission}'")
        return False

    def get_user_roles(self, user: str) -> List[str]:
        """
        Get roles assigned to a user.

        :param user: User identifier.
        :return: List of roles.
        """
        return self._user_roles.get(user, [])

    def get_role_permissions(self, role: str) -> List[str]:
        """
        Get permissions associated with a role.

        :param role: Role name.
        :return: List of permissions.
        """
        
        return self._roles_permissions.get(role, [])
