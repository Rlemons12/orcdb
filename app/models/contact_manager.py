"""
Contact Management System
Stores contacts and groups in JSON file (simple database)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class ContactManager:
    """Manages contacts and groups"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path.cwd() / "data" / "contacts.json"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database if doesn't exist
        if not self.db_path.exists():
            self._initialize_db()

        self.data = self._load()

    def _initialize_db(self):
        """Create initial database structure"""
        initial_data = {
            "contacts": [],
            "groups": [],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.db_path, 'w') as f:
            json.dump(initial_data, f, indent=2)

    def _load(self) -> dict:
        """Load database from file"""
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def _save(self):
        """Save database to file"""
        self.data['last_updated'] = datetime.now().isoformat()
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    # ========================================
    # CONTACT METHODS
    # ========================================

    def add_contact(self, name: str, email: str, title: str = "",
                   department: str = "", phone: str = "", notes: str = "") -> dict:
        """Add a new contact"""
        # Check if email already exists
        if any(c['email'].lower() == email.lower() for c in self.data['contacts']):
            raise ValueError(f"Contact with email {email} already exists")

        contact_id = len(self.data['contacts']) + 1
        contact = {
            "id": contact_id,
            "name": name,
            "email": email,
            "title": title,
            "department": department,
            "phone": phone,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self.data['contacts'].append(contact)
        self._save()
        return contact

    def get_contact(self, contact_id: int) -> Optional[dict]:
        """Get contact by ID"""
        for contact in self.data['contacts']:
            if contact['id'] == contact_id:
                return contact
        return None

    def get_all_contacts(self) -> List[dict]:
        """Get all contacts"""
        return self.data['contacts']

    def update_contact(self, contact_id: int, **kwargs) -> dict:
        """Update contact fields"""
        contact = self.get_contact(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        # Update allowed fields
        allowed_fields = ['name', 'email', 'title', 'department', 'phone', 'notes']
        for field, value in kwargs.items():
            if field in allowed_fields:
                contact[field] = value

        contact['updated_at'] = datetime.now().isoformat()
        self._save()
        return contact

    def delete_contact(self, contact_id: int):
        """Delete a contact"""
        self.data['contacts'] = [c for c in self.data['contacts'] if c['id'] != contact_id]

        # Remove from groups
        for group in self.data['groups']:
            if contact_id in group['member_ids']:
                group['member_ids'].remove(contact_id)

        self._save()

    def search_contacts(self, query: str) -> List[dict]:
        """Search contacts by name, email, or department"""
        query = query.lower()
        results = []
        for contact in self.data['contacts']:
            if (query in contact['name'].lower() or
                query in contact['email'].lower() or
                query in contact.get('department', '').lower()):
                results.append(contact)
        return results

    # ========================================
    # GROUP METHODS
    # ========================================

    def add_group(self, name: str, description: str = "", member_ids: List[int] = None) -> dict:
        """Add a new group"""
        # Check if group name already exists
        if any(g['name'].lower() == name.lower() for g in self.data['groups']):
            raise ValueError(f"Group with name '{name}' already exists")

        group_id = len(self.data['groups']) + 1
        group = {
            "id": group_id,
            "name": name,
            "description": description,
            "member_ids": member_ids or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self.data['groups'].append(group)
        self._save()
        return group

    def get_group(self, group_id: int) -> Optional[dict]:
        """Get group by ID"""
        for group in self.data['groups']:
            if group['id'] == group_id:
                return group
        return None

    def get_all_groups(self) -> List[dict]:
        """Get all groups"""
        return self.data['groups']

    def update_group(self, group_id: int, **kwargs) -> dict:
        """Update group fields"""
        group = self.get_group(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Update allowed fields
        allowed_fields = ['name', 'description', 'member_ids']
        for field, value in kwargs.items():
            if field in allowed_fields:
                group[field] = value

        group['updated_at'] = datetime.now().isoformat()
        self._save()
        return group

    def delete_group(self, group_id: int):
        """Delete a group"""
        self.data['groups'] = [g for g in self.data['groups'] if g['id'] != group_id]
        self._save()

    def add_member_to_group(self, group_id: int, contact_id: int):
        """Add a contact to a group"""
        group = self.get_group(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        contact = self.get_contact(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id} not found")

        if contact_id not in group['member_ids']:
            group['member_ids'].append(contact_id)
            group['updated_at'] = datetime.now().isoformat()
            self._save()

    def remove_member_from_group(self, group_id: int, contact_id: int):
        """Remove a contact from a group"""
        group = self.get_group(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if contact_id in group['member_ids']:
            group['member_ids'].remove(contact_id)
            group['updated_at'] = datetime.now().isoformat()
            self._save()

    def get_group_members(self, group_id: int) -> List[dict]:
        """Get all contacts in a group"""
        group = self.get_group(group_id)
        if not group:
            return []

        members = []
        for contact_id in group['member_ids']:
            contact = self.get_contact(contact_id)
            if contact:
                members.append(contact)
        return members

    def get_group_emails(self, group_id: int) -> List[str]:
        """Get all email addresses in a group"""
        members = self.get_group_members(group_id)
        return [m['email'] for m in members]

    # ========================================
    # UTILITY METHODS
    # ========================================

    def get_stats(self) -> dict:
        """Get database statistics"""
        return {
            "total_contacts": len(self.data['contacts']),
            "total_groups": len(self.data['groups']),
            "last_updated": self.data.get('last_updated', 'Unknown')
        }