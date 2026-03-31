// ===========================
// Contacts Management JavaScript
// ===========================

let allContacts = [];
let allGroups = [];
let currentGroupId = null;

// Load initial data
document.addEventListener('DOMContentLoaded', () => {
    loadContacts();
    loadGroups();
});

// ===========================
// Tab Management
// ===========================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// ===========================
// CONTACTS
// ===========================

async function loadContacts() {
    try {
        const response = await fetch('/contacts/api/contacts');
        allContacts = await response.json();

        document.getElementById('contactCount').textContent = allContacts.length;
        displayContacts(allContacts);
    } catch (error) {
        console.error('Error loading contacts:', error);
        document.getElementById('contactsList').innerHTML =
            '<p class="text-danger">Error loading contacts</p>';
    }
}

function displayContacts(contacts) {
    const container = document.getElementById('contactsList');

    if (contacts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-user-slash"></i>
                <p>No contacts found</p>
                <button class="btn btn-primary" onclick="showAddContactModal()">
                    Add Your First Contact
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="table-responsive">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Title</th>
                        <th>Department</th>
                        <th>Phone</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${contacts.map(contact => `
                        <tr>
                            <td><i class="fas fa-user"></i> ${contact.name}</td>
                            <td>${contact.email}</td>
                            <td>${contact.title || '-'}</td>
                            <td>${contact.department || '-'}</td>
                            <td>${contact.phone || '-'}</td>
                            <td>
                                <button class="btn btn-sm btn-info" onclick="editContact(${contact.id})" title="Edit">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteContact(${contact.id})" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function searchContacts() {
    const query = document.getElementById('contactSearch').value.toLowerCase();

    if (!query) {
        displayContacts(allContacts);
        return;
    }

    const filtered = allContacts.filter(contact =>
        contact.name.toLowerCase().includes(query) ||
        contact.email.toLowerCase().includes(query) ||
        (contact.department && contact.department.toLowerCase().includes(query))
    );

    displayContacts(filtered);
}

// ===========================
// Contact Modal
// ===========================

function showAddContactModal() {
    document.getElementById('contactModalTitle').innerHTML =
        '<i class="fas fa-user-plus"></i> Add Contact';
    document.getElementById('contactForm').reset();
    document.getElementById('contactId').value = '';
    document.getElementById('contactModal').classList.add('show');
}

function editContact(contactId) {
    const contact = allContacts.find(c => c.id === contactId);
    if (!contact) return;

    document.getElementById('contactModalTitle').innerHTML =
        '<i class="fas fa-user-edit"></i> Edit Contact';
    document.getElementById('contactId').value = contact.id;
    document.getElementById('contactName').value = contact.name;
    document.getElementById('contactEmail').value = contact.email;
    document.getElementById('contactTitle').value = contact.title || '';
    document.getElementById('contactDepartment').value = contact.department || '';
    document.getElementById('contactPhone').value = contact.phone || '';
    document.getElementById('contactNotes').value = contact.notes || '';

    document.getElementById('contactModal').classList.add('show');
}

function closeContactModal() {
    document.getElementById('contactModal').classList.remove('show');
}

async function saveContact(event) {
    event.preventDefault();

    const contactId = document.getElementById('contactId').value;
    const data = {
        name: document.getElementById('contactName').value,
        email: document.getElementById('contactEmail').value,
        title: document.getElementById('contactTitle').value,
        department: document.getElementById('contactDepartment').value,
        phone: document.getElementById('contactPhone').value,
        notes: document.getElementById('contactNotes').value
    };

    try {
        let response;
        if (contactId) {
            // Update existing contact
            response = await fetch(`/contacts/api/contacts/${contactId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        } else {
            // Create new contact
            response = await fetch('/contacts/api/contacts', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        }

        if (response.ok) {
            showNotification('Contact saved successfully!', 'success');
            closeContactModal();
            loadContacts();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to save contact', 'error');
        }
    } catch (error) {
        console.error('Error saving contact:', error);
        showNotification('Error saving contact', 'error');
    }
}

async function deleteContact(contactId) {
    if (!confirm('Are you sure you want to delete this contact?')) return;

    try {
        const response = await fetch(`/contacts/api/contacts/${contactId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Contact deleted', 'success');
            loadContacts();
        } else {
            showNotification('Failed to delete contact', 'error');
        }
    } catch (error) {
        console.error('Error deleting contact:', error);
        showNotification('Error deleting contact', 'error');
    }
}

// ===========================
// GROUPS
// ===========================

async function loadGroups() {
    try {
        const response = await fetch('/contacts/api/groups');
        allGroups = await response.json();

        document.getElementById('groupCount').textContent = allGroups.length;
        displayGroups(allGroups);
    } catch (error) {
        console.error('Error loading groups:', error);
        document.getElementById('groupsList').innerHTML =
            '<p class="text-danger">Error loading groups</p>';
    }
}

function displayGroups(groups) {
    const container = document.getElementById('groupsList');

    if (groups.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-users-slash"></i>
                <p>No groups found</p>
                <button class="btn btn-primary" onclick="showAddGroupModal()">
                    Create Your First Group
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = groups.map(group => `
        <div class="group-card">
            <div class="group-card-header">
                <h3><i class="fas fa-users"></i> ${group.name}</h3>
                <span class="badge badge-info">${group.member_count} members</span>
            </div>
            <p class="group-description">${group.description || 'No description'}</p>
            <div class="group-actions">
                <button class="btn btn-sm btn-primary" onclick="viewGroupDetails(${group.id})">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn btn-sm btn-info" onclick="editGroup(${group.id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm btn-success" onclick="emailGroupDirect(${group.id})">
                    <i class="fas fa-envelope"></i> Email
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteGroup(${group.id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

// ===========================
// Group Modal
// ===========================

async function showAddGroupModal() {
    document.getElementById('groupModalTitle').innerHTML =
        '<i class="fas fa-users"></i> Create Group';
    document.getElementById('groupForm').reset();
    document.getElementById('groupId').value = '';

    // Load contact checkboxes
    await loadMemberSelection();

    document.getElementById('groupModal').classList.add('show');
}

async function editGroup(groupId) {
    const response = await fetch(`/contacts/api/groups/${groupId}`);
    const group = await response.json();

    document.getElementById('groupModalTitle').innerHTML =
        '<i class="fas fa-users-cog"></i> Edit Group';
    document.getElementById('groupId').value = group.id;
    document.getElementById('groupName').value = group.name;
    document.getElementById('groupDescription').value = group.description || '';

    // Load contact checkboxes with pre-selected members
    await loadMemberSelection(group.member_ids);

    document.getElementById('groupModal').classList.add('show');
}

async function loadMemberSelection(selectedIds = []) {
    const container = document.getElementById('memberSelection');

    if (allContacts.length === 0) {
        await loadContacts();
    }

    if (allContacts.length === 0) {
        container.innerHTML = '<p>No contacts available. Add contacts first.</p>';
        return;
    }

    container.innerHTML = allContacts.map(contact => `
        <label class="checkbox-label">
            <input type="checkbox" 
                   name="groupMembers" 
                   value="${contact.id}"
                   ${selectedIds.includes(contact.id) ? 'checked' : ''}>
            <span>${contact.name} (${contact.email})</span>
        </label>
    `).join('');
}

function closeGroupModal() {
    document.getElementById('groupModal').classList.remove('show');
}

async function saveGroup(event) {
    event.preventDefault();

    const groupId = document.getElementById('groupId').value;
    const memberCheckboxes = document.querySelectorAll('input[name="groupMembers"]:checked');
    const memberIds = Array.from(memberCheckboxes).map(cb => parseInt(cb.value));

    const data = {
        name: document.getElementById('groupName').value,
        description: document.getElementById('groupDescription').value,
        member_ids: memberIds
    };

    try {
        let response;
        if (groupId) {
            // Update existing group
            response = await fetch(`/contacts/api/groups/${groupId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        } else {
            // Create new group
            response = await fetch('/contacts/api/groups', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
        }

        if (response.ok) {
            showNotification('Group saved successfully!', 'success');
            closeGroupModal();
            loadGroups();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to save group', 'error');
        }
    } catch (error) {
        console.error('Error saving group:', error);
        showNotification('Error saving group', 'error');
    }
}

async function deleteGroup(groupId) {
    if (!confirm('Are you sure you want to delete this group?')) return;

    try {
        const response = await fetch(`/contacts/api/groups/${groupId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('Group deleted', 'success');
            loadGroups();
        } else {
            showNotification('Failed to delete group', 'error');
        }
    } catch (error) {
        console.error('Error deleting group:', error);
        showNotification('Error deleting group', 'error');
    }
}

// ===========================
// View Group Details
// ===========================

async function viewGroupDetails(groupId) {
    try {
        const response = await fetch(`/contacts/api/groups/${groupId}`);
        const group = await response.json();

        currentGroupId = groupId;

        document.getElementById('viewGroupName').textContent = group.name;
        document.getElementById('viewGroupDescription').textContent =
            group.description || 'No description';
        document.getElementById('viewGroupMemberCount').textContent = group.members.length;

        const membersContainer = document.getElementById('viewGroupMembers');
        if (group.members.length === 0) {
            membersContainer.innerHTML = '<p>No members in this group</p>';
        } else {
            membersContainer.innerHTML = group.members.map(member => `
                <div class="member-item">
                    <i class="fas fa-user"></i>
                    <span>${member.name} (${member.email})</span>
                </div>
            `).join('');
        }

        document.getElementById('viewGroupModal').classList.add('show');
    } catch (error) {
        console.error('Error loading group details:', error);
        showNotification('Error loading group details', 'error');
    }
}

function closeViewGroupModal() {
    document.getElementById('viewGroupModal').classList.remove('show');
    currentGroupId = null;
}

// ===========================
// Email Group
// ===========================

async function emailGroupDirect(groupId) {
    currentGroupId = groupId;
    await emailGroup();
}

async function emailGroup() {
    if (!currentGroupId) return;

    try {
        const response = await fetch(`/contacts/api/groups/${currentGroupId}/emails`);
        const data = await response.json();

        if (data.emails.length === 0) {
            showNotification('This group has no members', 'error');
            return;
        }

        // Get group name
        const group = allGroups.find(g => g.id === currentGroupId);
        const groupName = group ? group.name : 'Group';

        // Pre-fill email in report generation modal
        closeViewGroupModal();
        document.getElementById('generateReportBtn').click();

        // Wait for modal to open, then populate email field
        setTimeout(() => {
            // This will be populated when user selects a report
            window.pendingGroupEmail = {
                emails: data.emails.join(', '),
                groupName: groupName
            };
        }, 100);

        showNotification(`Ready to email ${groupName} (${data.count} recipients)`, 'success');

    } catch (error) {
        console.error('Error getting group emails:', error);
        showNotification('Error getting group emails', 'error');
    }
}

// ===========================
// Notifications
// ===========================

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.375rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 2000;
        animation: slideInRight 0.3s;
        max-width: 400px;
    `;

    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}