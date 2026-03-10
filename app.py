from waitress import serve
from flask import Flask, request, jsonify,render_template,url_for,redirect,flash,Response,session
import mysql.connector
from mysql.connector import Error
import bcrypt
import os
import uuid
import csv
from decimal import Decimal
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps
from collections import defaultdict
from markupsafe import Markup
from datetime import datetime
import csv
import pandas as pd




app = Flask(__name__, template_folder="templates")
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = os.getenv("SECRET_KEY", "Cosmo or no other")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'  # Redirect to login page if not authenticated

class User(UserMixin):
    def __init__(self, user_id, username, role, email=None, name=None,status="Inactive"):
        self.id = user_id
        self.username = username
        self.role = role
        self.name = name
        self.email=email
        self.status = status

@login_manager.user_loader
def load_user(user_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if user_data:
        return User(
        user_id=user_data['user_id'],
        username=user_data['username'],
        role=user_data['role'],
        email=user_data['email'],
        name=user_data['name'],
        status=user_data['status']
    )

    return None

# Database connection
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # Changed to align with your usage
            password="Root!234",
            database="refund_app"
        )
        if connection.is_connected():
            print("Connection to the database was successful!")
        return connection
    except mysql.connector.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return connection
    
def role_required(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role not in allowed_roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('login_page'))  # Redirect to login page or a forbidden page
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/admin_page')
# @login_required
# @role_required(['Admin'])
def admin_page():
    return render_template('adminpage.html')

@app.route('/create_user', methods=['POST'])
# @login_required
# @role_required(['Admin'])
def create_user():
    try:
        data = request.json
        print(f"Received data: {data}")

        username = data['username']
        password = data['password']
        name = data['name']
        email = data['email']
        role = data['permission']  # `permission` from frontend corresponds to `role` in DB

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        connection = create_connection()
        if connection is None:
            print("Failed to connect to the database.")
            return jsonify({"error": "Database connection failed."}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO users (username, password, name, email, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, hashed_password, name, email, role))
        connection.commit()

        cursor.close()
        connection.close()
        return jsonify({"message": "User created successfully!"}), 201

    except Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred while creating the user."}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route('/list_users', methods=['GET'])
# @login_required
# @role_required(['Admin'])
def list_users():
    connection = create_connection()
    if connection is None:
        return jsonify({"error": "Failed to connect to the database."}), 500

    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT user_id, username, role, status, email, name FROM users
    """)
    users = cursor.fetchall()

    cursor.close()
    connection.close()
    return jsonify(users)

@app.route('/update_password', methods=['POST'])
# @login_required
# @role_required(['Admin'])
def update_password():
    data = request.json
    user_id = data['user_id']
    new_password = data['new_password']

    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", 
                   (hashed_password, user_id))
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Password updated successfully!"})

@app.route('/deactivate_user', methods=['POST'])
# @login_required
# @role_required(['Admin'])
def deactivate_user():
    data = request.json
    user_id = data.get('user_id')

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET status = 'inactive' WHERE user_id = %s", (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User has been deactivated successfully!"}), 200

@app.route('/activate_user', methods=['POST'])
# @login_required
# @role_required(['Admin'])
def activate_user():
    data = request.json
    user_id = data.get('user_id')

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE users SET status = 'active' WHERE user_id = %s", (user_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({"message": "User has been activated successfully!"}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        user_obj = User(
            user_id=user['user_id'],
            username=user['username'],
            role=user['role'],
            email=user['email'],
            name=user['name']
        )
        login_user(user_obj)  # Log the user in
    #     return jsonify({"message": "Login successful!"}), 200
    
    # else:
    #     return jsonify({"error": "Invalid username or password."}), 401
        if user['must_change_password']:
            return jsonify({"message": "Password change required", "must_change": True}), 200
        else:
            return jsonify({"message": "Login successful", "must_change": False}), 200

    return jsonify({"error": "Invalid username or password."}), 401

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_password = data['old_password']
    new_password = data['new_password']

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT password FROM users WHERE user_id = %s", (current_user.id,))
    user = cursor.fetchone()

    if not user or not bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Old password is incorrect"}), 400

    hashed_new = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute("""
        UPDATE users
        SET password = %s, must_change_password = FALSE
        WHERE user_id = %s
    """, (hashed_new, current_user.id))

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Password updated successfully"}), 200

def find_user_id_for_claim(role):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM users WHERE role = %s LIMIT 1", (role,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user["user_id"] if user else None
# Return user_id or None if no user found

# Set up the upload folder path
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/submit_claim', methods=['GET', 'POST'])
@login_required
# @role_required(['Customer Solution'])
def submit_claim():
    if request.method == 'POST':
        # === 1. Extract form data ===
        policy_holder_name = request.form.get('policy_holder_name')
        member_number = request.form.get('member_number')
        telephone = request.form.get('telephone')
        facility_attended = request.form.get('facility_attended')
        date_attended = request.form.get('date_attended')
        diagnosis = request.form.get('diagnosis')
        amount_claimed = request.form.get('amount_claimed')
        out_of_pocket_reason = request.form.get('out_of_pocket_reason')
        client_signature_name = request.form.get('client_signature_name')
        client_tel = request.form.get('client_tel')
        company_name = request.form.get('company_name')
        authorized_by = request.form.get('authorized_by')
        hr_signature_date = request.form.get('hr_signature_date')

        created_by = current_user.id  # Assumes user is logged in
        assigned_to = find_user_id_for_claim('Claims')

        # === 2. Database operations ===
        connection = create_connection()
        cursor = connection.cursor()

        try:
            # 1. Insert into refund_claims table
            cursor.execute("""
                INSERT INTO refund_claim (
                policy_holder_name, member_number, telephone, facility_attended,
                date_attended, diagnosis, amount_claimed, out_of_pocket_reason,
                client_signature_name, client_tel_number, company_name,
                authorized_by, hr_signature_date, status, assigned_to, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                 policy_holder_name, member_number, telephone, facility_attended,
                 date_attended, diagnosis, amount_claimed, out_of_pocket_reason,
                client_signature_name, client_tel, company_name,
                authorized_by, hr_signature_date, 'Pending Vetting', assigned_to, current_user.id
            ))
            claim_id = cursor.lastrowid
            
            # ✅ New: Insert initial claim_tracking record
            cursor.execute("""
            INSERT INTO claim_tracking (claim_id, status, remarks, updated_by, updated_at)
            VALUES (%s, %s, %s, %s,NOW())
            """, (claim_id, 'Pending Vetting', 'Refund submitted and awaiting vetting', current_user.id))

            # 2. Insert each claim item into the claim_items table
            claim_name_list = request.form.getlist('claim_name[]')
            policy_number_list = request.form.getlist('policy_number[]')
            amount_list = request.form.getlist('amount[]')
            facility_list = request.form.getlist('facility[]')
            date_attended_list = request.form.getlist('date_attended[]')

            for i in range(len(claim_name_list)):
                cursor.execute("""
                    INSERT INTO claim_items (
                        claim_id, member_name, policy_number, facility_name,
                        date_attended, amount_submitted
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    claim_id, claim_name_list[i], policy_number_list[i],
                    facility_list[i], date_attended_list[i], amount_list[i]
                ))

            # 3. Handle file uploads (if checked)
            upload_fields = ['prescription', 'lab_request', 'receipts', 'others']
            for field in upload_fields:
                file = request.files.get(f"{field}_file")
                if file and file.filename != '':
                    if allowed_file(file.filename):
                        # Generate a unique filename to avoid collisions
                        unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        file.save(file_path)

                        # Save attachment record
                        cursor.execute("""
                            INSERT INTO attachments (claim_id, file_path)
                            VALUES (%s, %s)
                        """, (claim_id, file_path))

            connection.commit()
            flash('Claim submitted successfully!', 'success')

        except Exception as e:
            print("Error:", e)
            connection.rollback()
            flash('Error submitting claim. Please try again.', 'danger')
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('submit_claim'))

    return render_template('submit_claim.html')

# Route to view all claims
@app.route('/view_claims')
@login_required
@role_required(['Admin','Claims', 'MD', 'Finance', 'Customer Solutions'])
def view_claims():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    # Workflow visibility based on role
    if current_user.role == "Claims":
        cursor.execute("SELECT * FROM refund_claim WHERE status = 'Pending Vetting'")
    elif current_user.role == "MD":
        cursor.execute("SELECT * FROM refund_claim WHERE status = 'Vetted'")
    elif current_user.role == "Finance":
        cursor.execute("SELECT * FROM refund_claim WHERE status = 'Pending Finance Processing'")
    else:
        # For other roles, show all or only their own submissions
        cursor.execute("SELECT * FROM refund_claim")

    claims = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('view_claims.html', claims=claims)



# Route to approve/reject a claim
@app.route('/approve_reject_claim/<int:claim_id>', methods=['GET', 'POST'])
@role_required(['Claims'])
@login_required
def approve_reject_claim(claim_id):
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        approval_status = request.form.get('approval_status')  # "approved" or "rejected"
        remarks = request.form.get('remarks')
        vetted_amount_input = request.form.get('vetted_amount')
        
        #Fetch original amount_claimed if vetted amount is blank
        cursor.execute("SELECT amount_claimed FROM refund_claim WHERE claim_id = %s",(claim_id,))
        original_claim = cursor.fetchone()
        original_amount = original_claim["amount_claimed"] if original_claim else None
        
        if vetted_amount_input:
            vetted_amount = Decimal(vetted_amount_input)
        else:
            # Default vetted_amount to original amount_claimed
            vetted_amount = original_amount

        # Logic for Claims team
        if approval_status == "approved":
            new_status = "Vetted"
        else:
            new_status = "Rejected by Claims"
            
        if approval_status == "approved":
            tracking_remarks = "Refund Vetted, awaiting MD approval"
        else:
            tracking_remarks = f"Rejected by Claims: {remarks}" if remarks else "Rejected by Claims"

        # Update claim status
        cursor.execute("""
            UPDATE refund_claim 
            SET status = %s, remarks = %s, vetted_amount = %s
            WHERE claim_id = %s
        """, (new_status, tracking_remarks, vetted_amount, claim_id))
        
        # Insert into claim_tracking
        cursor.execute("""
            INSERT INTO claim_tracking (claim_id, status, remarks, updated_by)
            VALUES (%s, %s, %s, %s)
        """, (claim_id, new_status, remarks, current_user.id))
        
        connection.commit()
        
        cursor.close()
        connection.close()

        flash(f'Claim {claim_id} updated by Claims team.', 'success')
        return redirect(url_for('view_claims'))

    # GET method
    cursor.execute("SELECT * FROM refund_claim WHERE claim_id = %s", (claim_id,))
    claim = cursor.fetchone()
    # Fetch attachments for this claim
    cursor.execute("SELECT file_path FROM attachments WHERE claim_id = %s", (claim_id,))
    attachments = cursor.fetchall()  # List of dicts with 'file_path'
    cursor.close()
    connection.close()

    return render_template('approve_reject_claim.html', claim=claim, attachments=attachments)


@app.route('/md_approve_reject_claim/<int:claim_id>', methods=['GET', 'POST'])
@login_required
@role_required(['MD'])
def md_approve_reject_claim(claim_id):
    if request.method == 'POST':
        approval_status = request.form.get('approval_status')  # e.g., "Pending Finance Processing" or "Rejected by MD"
        remarks = request.form.get('remarks')

        connection = create_connection()
        cursor = connection.cursor()
        
        if approval_status == "Pending Finance Processing":
            new_status = "Pending Finance Processing"
            md_status = "MD approved"
            tracking_remarks = "Refund approved by MD"
        else:
            new_status = "Rejected by MD"
            md_status = "Rejected by MD"
            tracking_remarks = f"Rejected by MD: {remarks}" if remarks else "Rejected by MD"

        # Update the claim with MD-specific data and global status
        cursor.execute("""
            UPDATE refund_claim 
            SET status = %s,
                md_status = %s,
                md_remarks = %s,
                md_by = %s,
                md_time = NOW()
            WHERE claim_id = %s
        """, (new_status, md_status, remarks, current_user.id, claim_id))

        # Log into claim_tracking
        cursor.execute("""
            INSERT INTO claim_tracking (claim_id, status, remarks, updated_by)
            VALUES (%s, %s, %s, %s)
        """, (claim_id, new_status, tracking_remarks, current_user.id))

        connection.commit()
        cursor.close()
        connection.close()

        flash(f'Claim {claim_id} updated by MD!', 'success')
        return redirect(url_for('view_claims'))

    # GET method
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM refund_claim WHERE claim_id = %s", (claim_id,))
    claim = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('md_approve_reject_claim.html', claim=claim)



@app.route('/finance_process_claim/<int:claim_id>', methods=['GET', 'POST'])
@login_required
@role_required(['Finance'])
def finance_process_claim(claim_id):
    if request.method == 'POST':
        payment_date = request.form.get('payment_date')
        amount_paid = request.form.get('amount_paid')
        remarks = request.form.get('remarks')

        connection = create_connection()
        cursor = connection.cursor()

        # Update claim while preserving MD information
        cursor.execute("""
            UPDATE refund_claim
            SET status = %s, payment_date = %s, amount_paid = %s, remarks = %s
            WHERE claim_id = %s
        """, ('Paid', payment_date, amount_paid, remarks, claim_id))

        # Insert into claim_tracking
        cursor.execute("""
            INSERT INTO claim_tracking (claim_id, status, remarks, updated_by)
            VALUES (%s, %s, %s, %s)
        """, (claim_id, 'Paid', remarks, current_user.id))

        connection.commit()
        cursor.close()
        connection.close()

        flash(f'Claim {claim_id} marked as Paid!', 'success')
        return redirect(url_for('view_claims'))

    # GET method
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM refund_claim WHERE claim_id = %s", (claim_id,))
    claim = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('finance_process_claim.html', claim=claim)



# Route for claim tracking
@app.route('/claim_tracking')
@login_required
@role_required(['Customer Solution'])
def claim_tracking():
    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT 
            ct.claim_id,
            rc.company_name,
            rc.policy_holder_name,
            ct.status,
            ct.remarks,
            u.name AS updated_by_name,
            ct.updated_at
        FROM claim_tracking ct
        JOIN refund_claim rc ON ct.claim_id = rc.claim_id
        LEFT JOIN users u ON ct.updated_by=u.user_id
        ORDER BY ct.updated_at DESC
    """)
    
    claims = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('tracking_claims.html', claims=claims)



# Route for downloading reports 
@app.route('/report_download', methods=['GET'])
@login_required
@role_required(['Admin', 'Claims', 'MD', 'Finance', 'Customer Solution'])
def report_download():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    company_name = request.args.get('company_name')

    # Step 1: Fetch claims
    query_claims = """
        SELECT rc.claim_id, rc.company_name, rc.policy_holder_name AS member_name,
               rc.facility_attended, rc.member_number, rc.amount_claimed, rc.amount_paid,
               rc.vetted_amount, rc.created_at
        FROM refund_claim rc
        WHERE 1=1
    """
    params = []

    if start_date and end_date:
        query_claims += " AND DATE(rc.created_at) BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    if company_name:
        query_claims += " AND rc.company_name = %s"
        params.append(company_name)

    query_claims += " ORDER BY rc.created_at DESC"

    connection = create_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query_claims, params)
    claims = cursor.fetchall()

    if not claims:
        cursor.close()
        connection.close()
        return render_template("report_downloading.html", report_generated=False, message="No claims found.")

    claim_map = {claim['claim_id']: claim for claim in claims}

    # Step 2: Fetch tracking data
    format_ids = ", ".join(["%s"] * len(claim_map))
    cursor.execute(f"""
        SELECT ct.claim_id, ct.status, ct.remarks, ct.updated_at, u.name AS updated_by
        FROM claim_tracking ct
        LEFT JOIN users u ON ct.updated_by = u.user_id
        WHERE ct.claim_id IN ({format_ids})
    """, list(claim_map.keys()))
    tracking_data = cursor.fetchall()
    cursor.close()
    connection.close()

    from collections import defaultdict
    tracking_by_claim = defaultdict(dict)
    for row in tracking_data:
        status = row['status']
        role = None
        if "Claims" in status or "Vetted" in status:
            role = "claims"
        elif "Pending Finance" in status or "MD" in status:
            role = "md"
        elif "Finance" in status or status == "Paid":
            role = "finance"
        if role:
            tracking_by_claim[row['claim_id']][role] = {
                "status": row["status"],
                "remarks": row["remarks"],
                "updated_by": row["updated_by"],
                "updated_at": row["updated_at"]
            }

    # Step 3: Assemble final report rows
    final_rows = []
    for claim_id, claim in claim_map.items():
        submitted_amount = float(claim["amount_claimed"] or 0)
        vetted_amount = float(claim.get("vetted_amount") or 0)
        paid_amount = float(claim.get("amount_paid") or 0)
        difference = vetted_amount - submitted_amount

        tr_claims = tracking_by_claim[claim_id].get("claims", {})
        tr_md = tracking_by_claim[claim_id].get("md", {})
        tr_fin = tracking_by_claim[claim_id].get("finance", {})

        row = [
            claim_id,
            claim["company_name"],
            claim["member_name"],
            claim["facility_attended"],
            claim["member_number"],
            submitted_amount,
            tr_claims.get("status", ""),
            tr_claims.get("remarks", ""),
            tr_claims.get("updated_by", ""),
            tr_claims.get("updated_at", ""),
            vetted_amount,
            difference,
            tr_md.get("status", ""),
            tr_md.get("remarks", ""),
            tr_md.get("updated_by", ""),
            tr_md.get("updated_at", ""),
            tr_fin.get("status", ""),
            tr_fin.get("remarks", ""),
            tr_fin.get("updated_by", ""),
            tr_fin.get("updated_at", ""),
            paid_amount
        ]
        final_rows.append(row)

    # Step 4: Headers
    headers = [
        "Claim ID", "Company", "Member", "Facility", "Member Number", "Submitted Amount",
        "Claims Status", "Claims Remarks", "Claims Handled By", "Claims Time", "Vetted Amount",
        "Difference (Vetted - Claimed)",
        "MD Status", "MD Remarks", "MD Handled By", "MD Time",
        "Finance Status", "Finance Remarks", "Finance Handled By", "Finance Time", "Paid Amount"
    ]

    # Step 5: Export to Excel
    import pandas as pd
    from datetime import datetime
    import os
    from markupsafe import Markup

    df = pd.DataFrame(final_rows, columns=headers)
    filename = f"refund_claims_detailed_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    filepath = os.path.join("static", "reports", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_excel(filepath, index=False)

    # Step 6: Render HTML table + download link
    html_table = Markup(df.to_html(classes="table table-striped table-bordered", index=False))
    return render_template(
        "report_downloading.html",
        report_generated=True,
        report_file_url=f"/static/reports/{filename}",
        html_table=html_table
    )



@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))





if __name__ == '__main__':
    app.run(debug=True)
