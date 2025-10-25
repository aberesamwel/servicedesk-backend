from flask import Flask
from app.routes.analytics import analytics_bp
from app.routes.export import export_bp
from app.routes.users import users_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(export_bp, url_prefix='/api/export')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)