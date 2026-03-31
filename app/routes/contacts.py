from flask import Blueprint, jsonify, request, render_template
from app.models.contact_manager import ContactManager

bp = Blueprint('contacts', __name__, url_prefix='/contacts')


# ========================================
# PAGE ROUTE
# ========================================

@bp.route('/')
def index():
    """Contacts management page"""
    return render_template('contacts.html')


# Initialize contact manager
contacts_db = ContactManager()


# ========================================
# CONTACT ROUTES
# ========================================

@bp.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    contacts = contacts_db.get_all_contacts()
    return jsonify(contacts)


@bp.route('/api/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get specific contact"""
    contact = contacts_db.get_contact(contact_id)
    if contact:
        return jsonify(contact)
    return jsonify({'error': 'Contact not found'}), 404


@bp.route('/api/contacts', methods=['POST'])
def add_contact():
    """Add new contact"""
    data = request.get_json()

    required = ['name', 'email']
    if not all(field in data for field in required):
        return jsonify({'error': 'Name and email are required'}), 400

    try:
        contact = contacts_db.add_contact(
            name=data['name'],
            email=data['email'],
            title=data.get('title', ''),
            department=data.get('department', ''),
            phone=data.get('phone', ''),
            notes=data.get('notes', '')
        )
        return jsonify(contact), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update contact"""
    data = request.get_json()

    try:
        contact = contacts_db.update_contact(contact_id, **data)
        return jsonify(contact)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@bp.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete contact"""
    try:
        contacts_db.delete_contact(contact_id)
        return jsonify({'message': 'Contact deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/contacts/search', methods=['GET'])
def search_contacts():
    """Search contacts"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = contacts_db.search_contacts(query)
    return jsonify(results)


# ========================================
# GROUP ROUTES
# ========================================

@bp.route('/api/groups', methods=['GET'])
def get_groups():
    """Get all groups"""
    groups = contacts_db.get_all_groups()

    # Add member count to each group
    for group in groups:
        group['member_count'] = len(group['member_ids'])

    return jsonify(groups)


@bp.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    """Get specific group with members"""
    group = contacts_db.get_group(group_id)
    if not group:
        return jsonify({'error': 'Group not found'}), 404

    # Add member details
    members = contacts_db.get_group_members(group_id)
    group['members'] = members
    group['member_count'] = len(members)

    return jsonify(group)


@bp.route('/api/groups', methods=['POST'])
def add_group():
    """Add new group"""
    data = request.get_json()

    if 'name' not in data:
        return jsonify({'error': 'Group name is required'}), 400

    try:
        group = contacts_db.add_group(
            name=data['name'],
            description=data.get('description', ''),
            member_ids=data.get('member_ids', [])
        )
        return jsonify(group), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    """Update group"""
    data = request.get_json()

    try:
        group = contacts_db.update_group(group_id, **data)
        return jsonify(group)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    """Delete group"""
    try:
        contacts_db.delete_group(group_id)
        return jsonify({'message': 'Group deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/groups/<int:group_id>/members', methods=['POST'])
def add_group_member(group_id):
    """Add member to group"""
    data = request.get_json()
    contact_id = data.get('contact_id')

    if not contact_id:
        return jsonify({'error': 'contact_id is required'}), 400

    try:
        contacts_db.add_member_to_group(group_id, contact_id)
        return jsonify({'message': 'Member added'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@bp.route('/api/groups/<int:group_id>/members/<int:contact_id>', methods=['DELETE'])
def remove_group_member(group_id, contact_id):
    """Remove member from group"""
    try:
        contacts_db.remove_member_from_group(group_id, contact_id)
        return jsonify({'message': 'Member removed'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@bp.route('/api/groups/<int:group_id>/emails', methods=['GET'])
def get_group_emails(group_id):
    """Get all email addresses in a group"""
    emails = contacts_db.get_group_emails(group_id)
    return jsonify({'emails': emails, 'count': len(emails)})


# ========================================
# STATS ROUTE
# ========================================

@bp.route('/api/contacts/stats', methods=['GET'])
def get_stats():
    """Get contact database statistics"""
    stats = contacts_db.get_stats()
    return jsonify(stats)