from datetime import datetime, date
from fileinput import filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import pdfkit
from flask import make_response
import os
from werkzeug.utils import secure_filename
import numpy as np
import torch
from torchvision import models, transforms
from PIL import Image
from groq import Groq
import openai
from deep_translator import GoogleTranslator
from flask import Flask, request, jsonify
#from googletrans import Translator, LANGUAGES
# import openai
app = Flask(__name__)
app.secret_key = 'wverihdfuvuwi2482'


# openai.api_key = "esecret_nqhhtffj88zp16fjcwpl33w8dh"
# openai.api_base = "https://api.endpoints.anyscale.com/v1"
# Initialize Groq client
client = Groq(api_key="FIXME")  # Replace with your actual key


app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="skin_db"
    )


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


import os
from werkzeug.utils import secure_filename

app.config['UPLOAD_FOLDER'] = 'static/profiles'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = 'static/profiles'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        password = request.form['password']
        dob  = request.form['dob']
        role = 'doctor'
        profile_image = request.files['profile_image']

        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(image_path)
        else:
            flash('Invalid image file.', 'danger')
            return redirect(request.url)

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (name, email, number, password, dob, role, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (name, email, number, hashed_password, dob, role, filename)
            )
            conn.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Email already exists.', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')



@app.route('/profile')
def profile():
    if 'email' not in session:
        flash('Please login to view your profile.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (session['email'],))
    user = cursor.fetchone()
   

    cursor.execute("SELECT * FROM prescriptions WHERE patient_id = %s ORDER BY created_at DESC", (user['id'],))

    detections = cursor.fetchall()

    conn.close()
    # print("USER ID:", user['id'])
    # print("DETECTIONS:", detections)

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    if user['role'] != 'user':
        flash("Unauthorized access to user profile.", "danger")
        return redirect(url_for('login'))

    return render_template('profile.html', user=user, detections=detections)


@app.route('/download_prescription/<int:prescription_id>')
def user_download_prescription(prescription_id):
    if 'email' not in session:
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    cursor.execute("SELECT * FROM users WHERE email = %s", (session['email'],))
    user = cursor.fetchone()

    if not user or user['role'] != 'user':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))


    cursor.execute("SELECT * FROM prescriptions WHERE id = %s AND patient_id = %s", (prescription_id, user['id']))
    prescription = cursor.fetchone()

    if not prescription:
        flash("Prescription not found.", "warning")
        return redirect(url_for('profile'))

    conn.close()

    html = render_template('prescription_pdf_single.html', user=user, prescription=prescription)
    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf')
    pdf = pdfkit.from_string(html, False, configuration=config)


    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=prescription_{user["name"]}_{prescription["id"]}.pdf'

    return response

@app.route('/nearby-hospitals')
def nearby_hospitals():
    return render_template('nearby_hospitals.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['email'] = user['email']
            session['role'] = user['role']
            session['name'] = user['name']
            flash('Login successful!', 'success')

          
            if user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')



class ResNet34(torch.nn.Module):
    def __init__(self, num_classes=8):
        super(ResNet34, self).__init__()
        self.network = models.resnet34(weights=None) 
        num_ftrs = self.network.fc.in_features
        self.network.fc = torch.nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.network(x)

model = ResNet34()
model.load_state_dict(torch.load('skin-cancer-resnet34.pth', map_location=torch.device('cpu')))
model.eval()


img_size = 224
imagenet_stats = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
preprocess = transforms.Compose([
    transforms.Resize(img_size),
    transforms.CenterCrop(img_size),
    transforms.ToTensor(),
    transforms.Normalize(*imagenet_stats)
])


class_info = {
    "Actinic keratosis": {
        "description": "Actinic keratosis is a precancerous skin condition caused by exposure to ultraviolet (UV) rays.",
        "symptoms": "Symptoms include rough, scaly patches on the skin, often on sun-exposed areas.",
        "treatment": "Treatment may involve cryotherapy, topical medications, or photodynamic therapy."
    },
    "Basal cell carcinoma": {
        "description": "Basal cell carcinoma is the most common type of skin cancer, often appearing as a waxy bump.",
        "symptoms": "Symptoms include a shiny, pearly bump or a bleeding or scabbing sore that heals and returns.",
        "treatment": "Treatment may involve surgical excision, Mohs surgery, or topical treatments."
    },
    "Benign keratosis": {
        "description": "Benign keratosis, also known as seborrheic keratosis, is a non-cancerous skin growth.",
        "symptoms": "Symptoms include raised, waxy, or wart-like growths on the skin.",
        "treatment": "Treatment is usually not necessary, but may involve removal if desired for cosmetic reasons."
    },
    "Dermatofibroma": {
        "description": "Dermatofibroma is a benign skin lesion that usually appears as a hard bump.",
        "symptoms": "Symptoms include a firm, round bump on the skin that may be red, pink, or brown.",
        "treatment": "Treatment is usually not necessary, but may involve removal if desired or if causing discomfort."
    },
    "Melanocytic nevus": {
        "description": "Melanocytic nevus, or mole, is a common benign skin growth made up of melanocytes.",
        "symptoms": "Symptoms include small, dark spots on the skin that may be raised or flat.",
        "treatment": "Treatment is usually not necessary, but moles may be removed if changing in size, shape, or color."
    },
    "Melanoma": {
        "description": "Melanoma is a type of skin cancer that develops from melanocytes, often appearing as a dark spot.",
        "symptoms": "Symptoms include changes in the size, shape, color, or feel of an existing mole, or the appearance of a new spot on the skin.",
        "treatment": "Treatment may involve surgical excision, immunotherapy, chemotherapy, or radiation therapy."
    },
    "Squamous cell carcinoma": {
        "description": "Squamous cell carcinoma is a common form of skin cancer, often appearing as a scaly patch or sore.",
        "symptoms": "Symptoms include a persistent, scaly red patch with irregular borders that may bleed or crust.",
        "treatment": "Treatment may involve surgical excision, Mohs surgery, or topical treatments."
    },
    "Vascular lesion": {
        "description": "Vascular lesions are abnormalities of the blood vessels, which can manifest as birthmarks or other skin discolorations.",
        "symptoms": "Symptoms vary depending on the type of vascular lesion and may include red or purple discolorations on the skin.",
        "treatment": "Treatment depends on the type and severity of the lesion, and may include laser therapy or surgical removal."
    }
}

def predict(image):
    image = Image.fromarray(np.array(image))

 
    if image.mode != 'RGB':
        image = image.convert('RGB')

    image = preprocess(image).unsqueeze(0)

    with torch.no_grad():
        outputs = model(image)
        _, predicted = torch.max(outputs, 1)
        prediction = list(class_info.keys())[predicted.item()]
        info = class_info[prediction]

    return prediction, info['description'], info['symptoms'], info['treatment']



@app.route('/detection', methods=['GET', 'POST'])
def detect():
 
    if 'email' not in session:
        flash('Please log in first', 'warning')
        return redirect(url_for('login')) 

    prediction = None
    description = symptoms = treatment = None
    image_url = None

    if request.method == 'POST':
        if 'image' not in request.files:
            return jsonify({"error": "No image part"})

        image = request.files['image']
        if image.filename == '':
            return jsonify({"error": "No selected file"})

        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        img = Image.open(filepath)
        prediction, description, symptoms, treatment = predict(img)

        image_url = f"profiles/{filename}"

    return render_template('detection.html',
                           prediction=prediction,
                           description=description,
                           symptoms=symptoms,
                           treatment=treatment,
                           image_url=image_url)

def translate_text(text, lang):
    try:
        if not text:
            return ""
        return GoogleTranslator(source='auto', target=lang).translate(text)
    except Exception as e:
        print(f"[Translation Error]: {e}")
        return "[Translation Failed]"

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json(force=True)
    print("Incoming translation request:", data)

    lang = data.get('lang', 'en')
    predect = data.get('predect', '')
    description = data.get('description', '')
    symptoms = data.get('symptoms', '')
    treatment = data.get('treatment', '')

    try:
        translated_predect = translate_text(predect, lang)
        translated_description = translate_text(description, lang)
        translated_symptoms = translate_text(symptoms, lang)
        translated_treatment = translate_text(treatment, lang)

        return jsonify({
            'predect': translated_predect,
            'description': translated_description,
            'symptoms': translated_symptoms,
            'treatment': translated_treatment
        })
    except Exception as e:
        print("Translation error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



############################## Doctor Dashboard################

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (session['email'],))
    doctor = cursor.fetchone()
    conn.close()

    return render_template('doctor_dashboard.html', doctor=doctor)


   

@app.route('/doctor/createuser', methods=['GET', 'POST'])
def doctor_create():
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        password = request.form['password']
        dob  = request.form['dob']
        role = 'user'
        profile_image = request.files['profile_image']

        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_image.save(image_path)
        else:
            flash('Invalid image file.', 'danger')
            return redirect(request.url)

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (name, email, number, password, dob, role, image_path) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (name, email, number, hashed_password, dob, role, filename)
            )
            conn.commit()
            flash('User created successfully.', 'success')  
            return redirect(url_for('doctor_create'))
        except mysql.connector.IntegrityError:
            flash('Email already exists.', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('doctor_createuser.html')




@app.route('/save-prescription', methods=['POST'])
def save_prescription():
    data = request.json
    patient_id = data.get('patient_id')
    medicine = data.get('medicine').strip().lower()
    dosage = data.get('dosage').strip().lower()
    notes = data.get('notes', '').strip().lower()

    if not patient_id or not medicine or not dosage:
        return jsonify({'error': 'Missing required fields!'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()


    cursor.execute(
        "INSERT INTO prescriptions (patient_id, medicine, dosage, notes, created_at) VALUES (%s, %s, %s, %s, %s)",
        (patient_id, medicine, dosage, notes, datetime.now())
    )
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'Prescription saved successfully!'}), 201




@app.route('/doctor/users')
def doctor_users():
    if session.get('role') != 'doctor':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)


    cursor.execute("SELECT * FROM users WHERE role NOT IN ('doctor')")
    users = cursor.fetchall()


    cursor.execute("""
        SELECT p.*, u.email 
        FROM prescriptions p
        JOIN users u ON p.patient_id = u.id
    """)
    detections = cursor.fetchall()

    detection_map = {}
    for row in detections:
        email = row['email']  
        detection_map.setdefault(email, []).append(row)
        

    conn.close()
    return render_template('doctor_userlist.html', users=users, detection_map=detection_map)

@app.route('/doctor/download_prescription/<int:user_id>')
def download_prescription(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM prescriptions WHERE patient_id = %s", (user_id,))
    prescriptions = cursor.fetchall()

    conn.close()

    html = render_template('prescription_pdf.html', user=user, prescriptions=prescriptions)


    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={user["name"]}.pdf'

    return response





@app.route('/doctor/edit_patient/<int:user_id>', methods=['GET', 'POST'])
def edit_patient(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Check if it's JSON (coming from sync)
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            number = data.get('number')
            dob = data.get('dob')
            cursor.execute("""
                UPDATE users SET name=%s, email=%s, number=%s, dob=%s WHERE id=%s
            """, (name, email, number, dob, user_id))
            conn.commit()
            return jsonify({"message": "Synced successfully"}), 200

        # Normal form POST (with file)
        name = request.form['name']
        email = request.form['email']
        number = request.form['number']
        dob = request.form['dob']
        profile_image = request.files.get('profile_image')
        if profile_image:
            filename = secure_filename(profile_image.filename)
            profile_image.save(os.path.join('static', 'profiles', filename))
            cursor.execute("UPDATE users SET image_path=%s WHERE id=%s", (filename, user_id))
            conn.commit()
        cursor.execute("""
            UPDATE users SET name=%s, email=%s, number=%s, dob=%s WHERE id=%s
        """, (name, email, number, dob, user_id))
        conn.commit()
        flash('Patient details updated successfully!', 'success')
        return redirect(url_for('doctor_users'))

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('edit_patient.html', user=user)




@app.route('/doctor/delete_patient/<int:user_id>', methods=['POST'])
def delete_patient(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    flash('Patient deleted successfully!', 'success')

    conn.close()
    return redirect(url_for('doctor_users'))


@app.route('/doctor/add_prescription/<int:user_id>', methods=['POST'])
def add_prescription(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    medicine = request.form['medicine']
    dosage = request.form['dosage']
    notes = request.form['notes']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO prescriptions (patient_id, medicine, dosage, notes) VALUES (%s, %s, %s, %s)",
                   (user_id, medicine, dosage, notes))
    conn.commit()
    flash('Prescription added successfully!', 'success')

    conn.close()
    return redirect(url_for('doctor_users'))

@app.route('/doctor/delete_prescription/<int:prescription_id>', methods=['POST'])
def delete_prescription(prescription_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM prescriptions WHERE id = %s", (prescription_id,))
    conn.commit()

    conn.close()
    flash('Prescription deleted successfully!', 'success')
    return redirect(request.referrer or url_for('doctor_users'))


@app.route('/doctor/view_prescriptions/<int:user_id>')
def view_prescriptions(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

  
    cursor.execute("""
        SELECT p.*, u.email, u.name 
        FROM prescriptions p
        JOIN users u ON p.patient_id = u.id
        WHERE p.patient_id = %s
    """, (user_id,))
    
    prescriptions = cursor.fetchall()

    conn.close()
    return render_template('view_prescriptions.html', prescriptions=prescriptions)

from flask import jsonify

@app.route('/doctor/ask_ai/<int:user_id>', methods=['GET', 'POST'])
def ask_ai(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        question = request.form['question']

        # Call your AI model here
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "user", "content": question}
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        answer = completion.choices[0].message.content

        # Return JSON for AJAX call
        return jsonify({'answer': answer})

    # On GET just render the template without any messages
    return render_template('ask_ai.html', user_id=user_id)


@app.route('/doctor/summarize_notes/<int:user_id>', methods=['GET'])
def summarize_notes(user_id):
    if session.get('role') != 'doctor':
        flash("Unauthorized access", "danger")
        return redirect(url_for('login'))

    # Connect to database and fetch all notes for the patient
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT notes FROM prescriptions WHERE patient_id = %s", (user_id,))
    results = cursor.fetchall()
    conn.close()

    if not results:
        flash("No notes found for this patient", "danger")
        return redirect(url_for('doctor_users'))

    # Combine all notes into a single string
    all_notes = "\n".join([row[0] for row in results if row[0]])

    # Summarize using Groq
    prompt = f"Summarize the following combined medical notes for a patient in 2 concise lines:\n\n{all_notes}"
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=150,
        top_p=1,
        stream=False
    )

    summary = completion.choices[0].message.content

    return render_template('summary_notes.html', summary=summary, notes=all_notes)
if __name__ == '__main__':
    app.run(debug=True)



