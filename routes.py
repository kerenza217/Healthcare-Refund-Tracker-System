from flask import render_template, request, redirect, url_for
from app import app, db
from models import RefundApplication, User
from flask_login import current_user


def find_user_id_for_claim(role):
    user = User.query.filter_by(role=role).first()  # Find the first user with the given role
    return user.user_id if user else None  # Return user_id or None if no user found

@app.route('/submit_claim', methods=['GET', 'POST'])
def submit_claim():
    if request.method == 'POST':
        # Process the submitted claim (Save to database)
        company_name = request.form.get('company_name')
        member_name = request.form.get('member_name')
        # Other form fields here...
        
        # Save to database (Placeholder)
        print(f"Claim submitted for {company_name} - {member_name}")

        return redirect(url_for('view_claims'))
    
    return render_template('submit_claim.html')

# Route to view all claims
@app.route('/view_claims')
def view_claims():
    # Fetch claims from database (Placeholder list)
    claims = [
        {'claim_id': 1, 'company_name': 'ABC Ltd', 'member_name': 'John Doe', 'status': 'Pending Vetting', 'created_at': '2025-03-14'}
    ]
    return render_template('view_claims.html', claims=claims)

# Route to approve/reject a claim
@app.route('/approve_reject_claim/<int:claim_id>', methods=['GET', 'POST'])
def approve_reject_claim(claim_id):
    if request.method == 'POST':
        approval_status = request.form.get('approval_status')
        remarks = request.form.get('remarks')
        
        # Update claim in database
        print(f"Claim {claim_id} updated: {approval_status} - {remarks}")

        return redirect(url_for('view_claims'))
    
    # Fetch claim details (Placeholder)
    claim = {'claim_id': claim_id, 'company_name': 'ABC Ltd', 'member_name': 'John Doe', 'status': 'Pending Vetting', 'amount': 500}
    
    return render_template('approve_reject_claim.html', claim=claim)

# Route for claim tracking
@app.route('/claim_tracking')
def claim_tracking():
    claims = [
        {'claim_id': 1, 'status': 'Approved', 'created_at': '2025-03-14', 'remarks': 'Approved by MD'}
    ]
    return render_template('claim_tracking.html', claims=claims)

# Route for downloading reports
@app.route('/report_download', methods=['GET'])
def report_download():
    # Process filters and generate report
    report_generated = False
    return render_template('report_download.html', report_generated=report_generated)

# if __name__ == '__main__':
#     app.run(debug=True)
