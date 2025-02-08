# Step 1: Import Required Libraries
from flask import Flask, request, jsonify  # Flask for creating APIs
import sqlite3  # To interact with the SQLite database
from datetime import datetime  # To handle timestamps

# Step 2: Initialize the Flask App
app = Flask(__name__)

# Step 3: Function to Connect to the Database
def get_db_connection():
    conn = sqlite3.connect('C:\\New folder\\sql\\employee_performance.db')  # Correct path
    conn.row_factory = sqlite3.Row
    return conn

# Step 4: Function to Calculate Performance Metrics
def calculate_performance(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate average resolution time
    cursor.execute('''
        SELECT AVG(ResolutionTime) FROM Tickets WHERE EmployeeID = ? AND Status = 'Closed'
    ''', (employee_id,))
    avg_resolution_time = cursor.fetchone()[0] or 0  # Default to 0 if no tickets are closed
    
    # Calculate total tickets solved
    cursor.execute('''
        SELECT COUNT(*) FROM Tickets WHERE EmployeeID = ? AND Status = 'Closed'
    ''', (employee_id,))
    total_tickets_solved = cursor.fetchone()[0]
    
    # Calculate efficiency score (example formula)
    efficiency_score = 100 / (avg_resolution_time or 1)  # Adjust formula as needed
    
    # Update PerformanceMetrics table
    cursor.execute('''
        INSERT OR REPLACE INTO PerformanceMetrics (EmployeeID, AverageResolutionTime, TotalTicketsSolved, EfficiencyScore)
        VALUES (?, ?, ?, ?)
    ''', (employee_id, avg_resolution_time, total_tickets_solved, efficiency_score))
    
    conn.commit()
    conn.close()

# Step 5: API to Log Ticket Start Time
@app.route('/start_ticket', methods=['POST'])
def start_ticket():
    data = request.json  # Get data from the request
    employee_id = data['employee_id']
    ticket_id = data['ticket_id']
    start_time = datetime.now()  # Current timestamp
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Tickets (TicketID, EmployeeID, StartTime, Status)
        VALUES (?, ?, ?, 'In Progress')
    ''', (ticket_id, employee_id, start_time))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Ticket started successfully'})

# Step 6: API to Log Ticket End Time and Calculate Performance
@app.route('/end_ticket', methods=['POST'])
def end_ticket():
    data = request.json
    employee_id = data['employee_id']
    ticket_id = data['ticket_id']
    end_time = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch start time
    cursor.execute('''
        SELECT StartTime FROM Tickets WHERE TicketID = ? AND EmployeeID = ?
    ''', (ticket_id, employee_id))
    start_time = cursor.fetchone()[0]
    
    # Calculate resolution time
    resolution_time = (end_time - datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')).total_seconds()
    
    # Update ticket with end time and resolution time
    cursor.execute('''
        UPDATE Tickets SET EndTime = ?, ResolutionTime = ?, Status = 'Closed'
        WHERE TicketID = ?
    ''', (end_time, resolution_time, ticket_id))
    conn.commit()
    conn.close()
    
    # Recalculate performance metrics
    calculate_performance(employee_id)
    
    return jsonify({'message': 'Ticket closed successfully'})

# Step 7: API to Get Performance Metrics
@app.route('/performance/<int:employee_id>', methods=['GET'])
def get_performance(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM PerformanceMetrics WHERE EmployeeID = ?
    ''', (employee_id,))
    performance_data = cursor.fetchone()
    conn.close()
    
    if performance_data:
        return jsonify({
            'EmployeeID': performance_data['EmployeeID'],
            'AverageResolutionTime': performance_data['AverageResolutionTime'],
            'TotalTicketsSolved': performance_data['TotalTicketsSolved'],
            'EfficiencyScore': performance_data['EfficiencyScore']
        })
    else:
        return jsonify({'message': 'No performance data found'})

# Step 8: Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)