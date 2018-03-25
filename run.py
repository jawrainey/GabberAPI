from gabber import create_app
import os

if __name__ == '__main__':
    app = create_app(os.environ.get('APP_MODE', 'dev'))
    app.run()
