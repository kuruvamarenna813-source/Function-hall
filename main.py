from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random key

bookings = []

hall_passwords = {
    'Bheemalingeshwara': 'hall1',
    'Panduranga': 'hall2',
    # Add more halls and passwords as needed
}

@app.route('/')
def homepage():
    return render_template('hall_pages/mainpage.html')

@app.route('/customer')
def customer():
    return render_template('hall_pages/customer.html')

@app.route('/select_hall/<hall_name>', methods=['POST'])
def select_hall(hall_name):
    session['hall'] = hall_name
    return redirect(url_for('booking_page'))

@app.route('/booking')
def booking_page():
    hall = session.get('hall', '')
    return render_template('hall_pages/booking.html', hall=hall)

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    data = request.form
    hall = session.get('hall', '')
    new_start = datetime.strptime(data['startDate'], '%Y-%m-%d')
    new_end = datetime.strptime(data['endDate'], '%Y-%m-%d')

    # Check for booking conflicts ignoring rejected bookings
    for booking in bookings:
        if booking['hall'] == hall and booking['status'] != 'Rejected':
            existing_start = datetime.strptime(booking['startDate'], '%Y-%m-%d')
            existing_end = datetime.strptime(booking['endDate'], '%Y-%m-%d')
            if new_start <= existing_end and new_end >= existing_start:
                error_msg = "On these dates, another customer has already booked the function hall."
                return render_template('hall_pages/booking.html', hall=hall, error=error_msg, form_data=data)

    # No conflicts, continue booking
    session['booking_data'] = {
        'hall': hall,
        'event': data['event'],
        'startDate': data['startDate'],
        'endDate': data['endDate'],
        'days': data['days'],
        'features': request.form.getlist('features')
    }
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        booking = session.get('booking_data')
        if booking:
            bookings.append({
                'user': name,
                'email': email,
                'hall': booking['hall'],
                'event': booking['event'],
                'startDate': booking['startDate'],
                'endDate': booking['endDate'],
                'days': booking['days'],
                'features': booking['features'],
                'status': 'Pending'  # initially pending, admin can accept/reject
            })
            session.pop('booking_data', None)
            return render_template('hall_pages/confirmation.html')
        else:
            return "No booking data found.", 400
    else:
        return render_template('hall_pages/loginpage.html', booking_data=session.get('booking_data'))

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        session['user'] = {'name': name, 'email': email}
        return redirect(url_for('user_dashboard'))
    return render_template('hall_pages/user_login.html')

@app.route('/user_dashboard')
def user_dashboard():
    user = session.get('user')
    if not user:
        return redirect(url_for('user_login'))
    return render_template('hall_pages/user_dashboard.html', user=user)

@app.route('/user_logout')
def user_logout():
    session.pop('user', None)
    return redirect(url_for('homepage'))

@app.route('/user_profile')
def user_profile():
    user = session.get('user')
    if not user:
        return redirect(url_for('user_login'))
    # Potential future enhancements for profile
    return render_template('hall_pages/user_profile.html', user=user)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        hall = request.form.get('hall')
        password = request.form.get('password')
        if hall_passwords.get(hall) == password:
            hall_bookings = [b for b in bookings if b['hall'] == hall]
            return render_template('hall_pages/adminB.html', bookings=hall_bookings, hall=hall)
        else:
            return "Invalid password.", 403
    return render_template('hall_pages/admin_login.html')

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    new_status = data.get('status')

    for b in bookings:
        if b['user'] == name and b['email'] == email:
            b['status'] = new_status
            return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/booking_status', methods=['GET', 'POST'])
def booking_status():
    user = session.get('user')
    user_status = None
    if user:
        name = user['name']
        email = user['email']
        for b in reversed(bookings):
            if b['user'] == name and b['email'] == email:
                user_status = b
                break
    elif request.method == 'POST':
        # Optional: fallback to posted data if session not found
        name = request.form.get('name')
        email = request.form.get('email')
        for b in reversed(bookings):
            if b['user'] == name and b['email'] == email:
                user_status = b
                break
    return render_template('hall_pages/booking_status.html', booking=user_status)

if __name__ == '__main__':
    app.run(debug=True)
