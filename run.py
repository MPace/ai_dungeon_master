"""
Application entry point
"""
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Get port and host from environment variables
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Run the app
    app.run(debug=app.config['DEBUG'], host=host, port=port)