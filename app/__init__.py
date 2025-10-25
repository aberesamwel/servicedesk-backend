from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    
    # CORS configuration
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Register blueprints
    from app.routes.tickets import tickets_bp
    from app.routes.users import users_bp
    from app.routes.agents import agents_bp
    from app.routes.messages import messages_bp
    from app.routes.analytics import analytics_bp
    from app.routes.auth import auth_bp
    from app.routes.export import export_bp
    from app.routes.sla import sla_bp
    from app.routes.files import files_bp
    
    app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(sla_bp, url_prefix='/api/sla')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}
    
    return app