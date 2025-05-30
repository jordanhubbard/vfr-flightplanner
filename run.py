from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    app.run(debug=True, use_reloader=True, host='0.0.0.0', port=port)
