import os
from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import pandas as pd

app = Flask(__name__)

DATABASE = 'doctors.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS doctors (id INTEGER PRIMARY KEY, name TEXT, area TEXT, area_specified TEXT, wa TEXT, link TEXT)''')
        conn.commit()
        conn.close()

def add_doctor(name, area,area_specified,wa, link):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO doctors (name, area, area_specified,wa, link) VALUES (?, ?, ?, ?,?)", (name, area, area_specified,wa, link))
    conn.commit()
    conn.close()

def delete_doctor(doctor_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM doctors WHERE id=?", (doctor_id,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, name, area, area_specified, wa, link FROM doctors")
    doctors = [{'id': row[0], 'name': row[1], 'area': row[2], 'wa': row[4], 'link': row[5]} for row in c.fetchall()]
    c.execute("SELECT DISTINCT area FROM doctors")
    areas = [row[0] for row in c.fetchall()]
    conn.close()
    return render_template('index.html', doctors=doctors, areas=areas)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        process_file(filepath)
        return redirect(url_for('index'))

def process_file(filepath):
    df = pd.read_excel(filepath, sheet_name="Website")
    for index, row in df.iterrows():
        name = row['Name'].upper()
        for i in range(1,12):
            if f'Area {i}' in row['Area']:
                area = f'Area {i}'
                break
            else:
                area='Unknown'
        link = 'N/A'
        area_specific=row['Area'][7:].lower()
        wa=row['wa'].strip('+88')
        add_doctor(name, area, area_specific,wa, link)
    os.remove(filepath)

@app.route('/delete_doctor/<int:doctor_id>', methods=['POST'])
def delete_doctor_view(doctor_id):
    delete_doctor(doctor_id)
    return redirect(url_for('index'))

@app.route('/update_resume/<int:doctor_id>', methods=['GET', 'POST'])
def update_resume(doctor_id):
    if request.method == 'POST':
        new_link = request.form['new_link']
        update_resume_link(doctor_id, new_link)
        return redirect(url_for('index'))
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT name, link FROM doctors WHERE id=?", (doctor_id,))
        doctor = c.fetchone()
        conn.close()
        if doctor:
            return render_template('update_resume.html', doctor_id=doctor_id, doctor_name=doctor[0], current_link=doctor[1])
        else:
            return "Doctor not found"

def update_resume_link(doctor_id, new_link):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if new_link!='N/A':
        c.execute("UPDATE doctors SET link=? WHERE id=?", (f'{new_link}', doctor_id))
    else:
        c.execute("UPDATE doctors SET link=? WHERE id=?", (f'N/A', doctor_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    app.run(debug=True,template_folder='Templates')
