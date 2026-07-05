import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables FIRST before importing any other modules
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.user import db
from src.routes.user import user_bp
from src.routes.betting import betting_bp
from src.routes.enhanced_betting import enhanced_betting_bp
from src.routes.espn_style import espn_style_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')

# Enable CORS for all routes
CORS(app, origins="*")

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(betting_bp, url_prefix='/api/betting')
app.register_blueprint(enhanced_betting_bp, url_prefix='/api/enhanced')
app.register_blueprint(espn_style_bp, url_prefix='/api/espn')

# Try to import and register realtime betting routes if available
try:
    from src.routes.realtime_betting import realtime_betting_bp
    app.register_blueprint(realtime_betting_bp, url_prefix='/api/realtime')
    
    # Initialize realtime service with Socket.IO
    from src.services.realtime_service import RealtimeService
    realtime_service = RealtimeService(
        socketio=socketio,
        odds_api_key=os.getenv('ODDS_API_KEY'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    print("Real-time Socket.IO service initialized successfully")
    
except ImportError as e:
    print(f"Warning: Could not import realtime_betting: {e}")
    print("Real-time features will be disabled")
except Exception as e:
    print(f"Warning: Could not initialize realtime service: {e}")
    print("Real-time features will be disabled")

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Static file serving (MUST be after blueprint registration)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nServer shutdown complete")
