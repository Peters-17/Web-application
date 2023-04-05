# project: p4
# submitter: hyuan73@wisc.edu
# partner: none
# hours: 15

# import statements
import pandas as pd
from flask import Flask, request, jsonify
import re
import time
import random
from flask import Flask, request, render_template, Response
import matplotlib.pyplot as plt
import io
from io import BytesIO
import base64
import flask
import matplotlib
matplotlib.use('Agg')

#Source: https://data.dhsgis.wi.gov/
app = Flask(__name__)

counts = 1
countA = 0
countB = 0

# Initialize a set to keep track of the IP addresses that have visited the browse.json resource
visitors = []

# Initialize a dictionary to keep track of the last request time for each IP address
last_request_time = {}

@app.route('/')
def home():
    global counts
    ratioA =countA/counts
    ratioB =countB/counts
    
    with open("index.html") as f:
        html = f.read()        
    if counts < 11:
        if (counts % 2) == 0:
            counts += 1
            return html.replace(
                '<a href="donate.html">donate</a><br><br>',
                '<a style="background-color:red;border-color:red" href="donate.html?from=A">donate</a><br><br>')
        else:
            counts += 1
            return html.replace(
                '<a href="donate.html">donate</a><br><br>',
                '<a style="background-color:green;border-color:blue" href="donate.html?from=B">donate</a><br><br>')
    else:
        if ratioA >= ratioB:
            with open("index.html") as f:
                html = f.read()
                return html.replace('<a href="donate.html">donate</a><br><br>',
                '<a style="background-color:red;border-color:red" href="donate.html?from=A">donate</a><br><br>')
        else:
            with open("index.html") as f:
                html = f.read()
                return html.replace(
                '<a href="donate.html">donate</a><br><br>',
                '<a style="background-color:green;border-color:blue" href="donate.html?from=B">donate</a><br><br>')
            
@app.route('/browse.html')
def browse_handler():
    # Load the 100 rows data from main.csv into a DataFrame
    df = pd.read_csv('main.csv')

    df.insert(loc=0, column='', value=df.index + 1)
    
    # Convert the DataFrame to an HTML table
    table_html = df.to_html(index=False)
    
    # Generate the complete HTML page with the table in it
    html = "<html><head><title>Browse Data</title></head><body>"
    html += "<h1>Data from main.csv</h1>"
    html += table_html
    html += "</body></html>"

    # Return the HTML page as a string
    return html

@app.route('/email', methods=["POST"])
def email():
    global num_subscribed
    try:
        with open("emails.txt","r") as f:
            num_subscribed = sum(1 for line in f if line.rstrip()) 
 
    except:
        num_subscribed = 0
        
    email = str(request.data, "utf-8")
    suffix = r"\.(edu|com|org|net|io)"
    at = r"(@|[aA][tT][AT])"
    opt_brackets = r"[\(\)\{\}\[\]]?"
  
    if re.match(r"(\w+)\s*" + opt_brackets + at + opt_brackets + r"\s*(\w+)" + suffix + r"(?<!\.com\.com)$", email):
        with open("emails.txt", "a") as f:
            f.write(email + "\n")
            num_subscribed += 1
        return jsonify(f"thanks, your subscriber number is {num_subscribed}!")
    return jsonify("Please enter a valid email address.")

@app.route('/donate.html')
def donate():
    global countA
    global countB
    with open("donate.html") as f:
        html = f.read()    
    if counts < 11:
        if request.args.get("from")=="A":
            countA += 1
        else:
            countB += 1
    return html


#individual part


@app.route('/browse.json')
def browse_json():
    """Return the browse data in JSON format"""
    df = pd.read_csv('main.csv')
    #data = df.to_dict(orient='records')
    global last_request_time
    client_ip = request.remote_addr
    list_of_dicts = df.to_dict(orient='records')
    # list of dicts, each idx is a row
    if not client_ip in last_request_time:
        # add
        last_request_time[client_ip] = time.time()
        return jsonify(list_of_dicts)
    else:
        # check time
        myTime = time.time()
        if myTime - last_request_time[client_ip] < 60:
            # go awway
            return flask.Response("<b>go away</b>",
                              status=429,
                              headers={"Retry-After": "60"})
        else:
            last_request_time[client_ip] = myTime
        return jsonify(list_of_dicts)

@app.route('/visitors.json')
def visitors_json():
    """Return the list of IP addresses that have visited the browse.json resource"""
    for k,v in last_request_time.items():
        visitors.append(k)
    return visitors

# individual part2:
# Use histogram
@app.route('/dashboard_1.svg')
@app.route('/dashboard_1.svg?bins=100')
def dashboard_1():
    """Generate and return a histogram plot of column A vs column B"""
    df = pd.read_csv('main.csv')
    fig, ax = plt.subplots()
    if request.args.get("bins") != None:
        ax.hist(df['TESTS_POS_CONF_7DAYAVG'], bins=int(request.args.get("bins")))
    else:
        ax.hist(df['TESTS_POS_CONF_7DAYAVG'])
    ax.set_xlabel('TESTS_POS_CONF_7DAYAVG')
    ax.set_ylabel('NUMBER_POS')
    buffer = BytesIO()
    plt.savefig(buffer, format='svg')
    svg_data = buffer.getvalue()
    plt.close(fig)
    return Response(buffer.getvalue(),
                     headers={"Content-Type": "image/svg+xml"})

# Use scatter
@app.route('/dashboard_2.svg')
def dashboard_2():
    """Generate and return a scatter plot of column A vs column B"""
    df = pd.read_csv('main.csv')
    fig, ax = plt.subplots()
    ax.scatter(df['NEG_NEW'], df['NEG_7DAYAVG'])
    ax.set_xlabel('NEG_NEW')
    ax.set_ylabel('NEG_7DAYAVG')
    buffer = BytesIO()
    plt.savefig(buffer, format='svg')
    svg_data = buffer.getvalue()
    plt.close(fig)
    return Response(buffer.getvalue(),
                     headers={"Content-Type": "image/svg+xml"})
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) # don't change this line!

# NOTE: app.run never returns (it runs for ever, unless you kill the process)
# Thus, don't define any functions after the app.run call, because it will
# never get that far.