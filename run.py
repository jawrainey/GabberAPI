from gabber import create_app
import os

app = create_app(os.environ.get('APP_MODE', 'default'))

if __name__ == '__main__':
    app.run()
