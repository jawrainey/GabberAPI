from gabber import create_app
import os

app = create_app(os.environ.get('APP_MODE', 'dev'))

if __name__ == '__main__':
    app.run()
