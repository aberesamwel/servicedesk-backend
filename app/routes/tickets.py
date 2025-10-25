from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket import Ticket, TicketActivity
from app.schemas.ticket_schema import ticket_schema, tickets_schema
from app.services.assignment_service import AssignmentService
from datetime import datetime
import uuid 

tickets_bp = Blueprint('tickets', __name__)

@tickets_bp.route('/', methods=['GET'])
def get_tickets():
    """Get all tickets with optional filtering and real-time SLA calculation"""
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to = request.args.get('assigned_to')
    created_by = request.args.get('created_by')
    
    query = Ticket.query
    
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if assigned_to:
        query = query.filter(Ticket.assigned_to == assigned_to)
    if created_by:
        query = query.filter(Ticket.created_by == created_by)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    # Real-time SLA violation check for open tickets
    for ticket in tickets:
        if ticket.status != 'Closed':
            ticket.sla_violated = ticket.check_sla_violation()
    
    db.session.commit()
    
    return jsonify(tickets_schema.dump(tickets))

@tickets_bp.route('/<ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    """Get a specific ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Update SLA violation status
    if ticket.status != 'Closed':
        ticket.sla_violated = ticket.check_sla_violation()
        db.session.commit()
    
    return jsonify(ticket_schema.dump(ticket))

@tickets_bp.route('/', methods=['POST'])
def create_ticket():
    """Create a new ticket"""
    data = request.get_json()
    
    # Generate ticket ID
    ticket_count = Ticket.query.count() + 1
    ticket_id = f"TKT-{ticket_count:04d}"
    
    ticket = Ticket(
        id=ticket_id,
        title=data['title'],
        description=data['description'],
        priority=data.get('priority', 'Medium'),
        category=data['category'],
        created_by=data['created_by']
    )
    
    db.session.add(ticket)
    db.session.flush()  # Get ticket ID before auto-assignment
    
    # Auto-assign to agent with least workload
    AssignmentService.auto_assign_ticket(ticket)
    
    db.session.commit()
    
    return jsonify(ticket_schema.dump(ticket)), 201

@tickets_bp.route('/<ticket_id>', methods=['PUT'])
def update_ticket(ticket_id):
    """Update a ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    old_status = ticket.status
    old_priority = ticket.priority
    old_assigned_to = ticket.assigned_to
    
    # Update fields
    for field in ['title', 'description', 'status', 'priority', 'assigned_to', 'category']:
        if field in data:
            setattr(ticket, field, data[field])
    
    ticket.updated_at = datetime.utcnow()
    
    # Handle status change to Closed
    if data.get('status') == 'Closed' and old_status != 'Closed':
        ticket.resolved_at = datetime.utcnow()
        ticket.resolution_time_hours = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
    
    # Log activities for changes
    activities = []
    
    if 'status' in data and data['status'] != old_status:
        activity = TicketActivity(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            activity_type='status_change',
            description=f'Status changed from {old_status} to {data["status"]}',
            performed_by=data.get('performed_by', 'system'),
            performed_by_name=data.get('performed_by_name', 'System')
        )
        activities.append(activity)
    
    if 'priority' in data and data['priority'] != old_priority:
        activity = TicketActivity(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            activity_type='priority_change',
            description=f'Priority changed from {old_priority} to {data["priority"]}',
            performed_by=data.get('performed_by', 'system'),
            performed_by_name=data.get('performed_by_name', 'System')
        )
        activities.append(activity)
    
    if 'assigned_to' in data and data['assigned_to'] != old_assigned_to:
        if data['assigned_to']:
            description = f'Ticket assigned to agent {data["assigned_to"]}'
        else:
            description = 'Ticket unassigned'
        
        activity = TicketActivity(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            activity_type='assignment',
            description=description,
            performed_by=data.get('performed_by', 'system'),
            performed_by_name=data.get('performed_by_name', 'System')
        )
        activities.append(activity)
    
    for activity in activities:
        db.session.add(activity)
    
    db.session.commit()
    
    return jsonify(ticket_schema.dump(ticket))

@tickets_bp.route('/<ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Delete a ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    
    return '', 204

@tickets_bp.route('/analytics/sla-adherence', methods=['GET'])
def get_sla_adherence():
    """Get SLA adherence analytics - ALL tickets in system"""
    all_tickets = Ticket.query.all()
    
    if not all_tickets:
        return jsonify({
            'total_tickets': 0,
            'met_sla': 0,
            'violated_sla': 0,
            'adherence_percentage': 0
        })
    
    met_sla = len([t for t in all_tickets if not t.sla_violated])
    violated_sla = len([t for t in all_tickets if t.sla_violated])
    adherence_percentage = (met_sla / len(all_tickets)) * 100
    
    return jsonify({
        'total_tickets': len(all_tickets),
        'met_sla': met_sla,
        'violated_sla': violated_sla,
        'adherence_percentage': round(adherence_percentage, 2)
    })

@tickets_bp.route('/analytics/aging', methods=['GET'])
def get_ticket_aging():
    """Get ticket aging analysis"""
    open_tickets = Ticket.query.filter(Ticket.status != 'Closed').all()
    
    aging_buckets = {
        '0-24 hours': [],
        '24-48 hours': [],
        '48-72 hours': [],
        '72+ hours': []
    }
    
    for ticket in open_tickets:
        hours_open = ticket.hours_open
        
        if hours_open < 24:
            aging_buckets['0-24 hours'].append(ticket)
        elif hours_open < 48:
            aging_buckets['24-48 hours'].append(ticket)
        elif hours_open < 72:
            aging_buckets['48-72 hours'].append(ticket)
        else:
            aging_buckets['72+ hours'].append(ticket)
    
    result = {}
    for bucket, tickets in aging_buckets.items():
        result[bucket] = {
            'count': len(tickets),
            'tickets': tickets_schema.dump(tickets)
        }
    
    return jsonify(result)