from flask import Blueprint, request, jsonify, make_response
from app.models.ticket import Ticket
from app.schemas.ticket_schema import tickets_schema
import csv
from io import StringIO, BytesIO
from datetime import datetime

export_bp = Blueprint('export', __name__)

@export_bp.route('/tickets/excel', methods=['GET'])
def export_tickets_excel():
    """Enhanced CSV export with custom date range filters"""
    status = request.args.get('status')
    priority = request.args.get('priority')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    assigned_to = request.args.get('assigned_to')
    
    query = Ticket.query
    
    # Apply filters
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if category:
        query = query.filter(Ticket.category == category)
    if assigned_to:
        query = query.filter(Ticket.assigned_to == assigned_to)
    if start_date:
        query = query.filter(Ticket.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Ticket.created_at <= datetime.fromisoformat(end_date))
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Enhanced headers
    writer.writerow([
        'ID', 'Title', 'Status', 'Priority', 'Category', 
        'Assigned To', 'Created By', 'Created At', 'Updated At',
        'Hours Open', 'SLA Violated', 'Resolution Time'
    ])
    
    for ticket in tickets:
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.status,
            ticket.priority,
            ticket.category,
            ticket.assigned_to or 'Unassigned',
            ticket.created_by,
            ticket.created_at.strftime('%Y-%m-%d %H:%M'),
            ticket.updated_at.strftime('%Y-%m-%d %H:%M'),
            f"{ticket.hours_open:.1f}",
            'Yes' if ticket.sla_violated else 'No',
            f"{ticket.resolution_time_hours:.1f}h" if ticket.resolution_time_hours else 'N/A'
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=tickets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response

@export_bp.route('/tickets/pdf', methods=['GET'])
def export_tickets_pdf():
    """Export tickets to PDF format with ReportLab"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        return jsonify({'error': 'ReportLab not installed. Install with: pip install reportlab'}), 400
    
    status = request.args.get('status')
    priority = request.args.get('priority')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Ticket.query
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if start_date:
        query = query.filter(Ticket.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Ticket.created_at <= datetime.fromisoformat(end_date))
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("IT ServiceDesk Tickets Report", styles['Title'])
    
    # Report info
    report_info = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
    
    # Table data
    data = [['ID', 'Title', 'Status', 'Priority', 'Created']]
    for ticket in tickets:
        data.append([
            ticket.id,
            ticket.title[:30] + '...' if len(ticket.title) > 30 else ticket.title,
            ticket.status,
            ticket.priority,
            ticket.created_at.strftime('%Y-%m-%d')
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Build PDF
    story = [title, Spacer(1, 12), report_info, Spacer(1, 12), table]
    doc.build(story)
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=tickets_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

@export_bp.route('/templates', methods=['GET'])
def get_export_templates():
    """Get available export templates"""
    templates = [
        {
            'id': 'summary',
            'name': 'Summary Report',
            'description': 'High-level ticket statistics',
            'formats': ['pdf', 'csv']
        },
        {
            'id': 'detailed',
            'name': 'Detailed Report',
            'description': 'Complete ticket information',
            'formats': ['csv', 'excel']
        },
        {
            'id': 'sla',
            'name': 'SLA Compliance Report',
            'description': 'SLA performance metrics',
            'formats': ['pdf']
        },
        {
            'id': 'agent_performance',
            'name': 'Agent Performance Report',
            'description': 'Agent productivity metrics',
            'formats': ['pdf', 'csv']
        }
    ]
    return jsonify(templates)