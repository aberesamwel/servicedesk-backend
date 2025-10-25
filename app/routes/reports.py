from flask import Blueprint, request, jsonify
from app.services.report_service import ReportService
from app.utils.cache_manager import cache_manager

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/summary', methods=['GET'])
def get_summary_report():
    """Get summary report with caching"""
    days = request.args.get('days', 30, type=int)
    cache_key = f"summary_report_{days}"
    
    # Check cache first
    cached_report = cache_manager.get(cache_key)
    if cached_report:
        return jsonify(cached_report)
    
    # Generate report
    report = ReportService.generate_summary_report(days)
    
    # Cache for 1 hour
    cache_manager.set(cache_key, report, 3600)
    
    return jsonify(report)

@reports_bp.route('/agent-performance', methods=['GET'])
def get_agent_performance_report():
    """Get agent performance report"""
    days = request.args.get('days', 30, type=int)
    cache_key = f"agent_performance_{days}"
    
    cached_report = cache_manager.get(cache_key)
    if cached_report:
        return jsonify(cached_report)
    
    report = ReportService.generate_agent_performance_report(days)
    cache_manager.set(cache_key, report, 1800)  # 30 minutes
    
    return jsonify(report)

@reports_bp.route('/sla-compliance', methods=['GET'])
def get_sla_compliance_report():
    """Get SLA compliance report"""
    days = request.args.get('days', 30, type=int)
    cache_key = f"sla_compliance_{days}"
    
    cached_report = cache_manager.get(cache_key)
    if cached_report:
        return jsonify(cached_report)
    
    report = ReportService.generate_sla_compliance_report(days)
    cache_manager.set(cache_key, report, 3600)
    
    return jsonify(report)

@reports_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    return jsonify(cache_manager.get_stats())

@reports_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear report cache"""
    pattern = request.json.get('pattern', '*_report_*')
    cleared = cache_manager.clear_pattern(pattern)
    
    return jsonify({
        'message': f'Cleared {cleared} cache entries',
        'pattern': pattern
    })