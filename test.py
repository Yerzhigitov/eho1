from flask import Flask, render_template
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

@app.route('/')
def test():
    return render_template('eko.html')

if __name__ == '__main__':
    print("Текущая директория:", os.getcwd())
    print("Папка шаблонов:", app.template_folder)
    app.run(debug=True, port=5000)