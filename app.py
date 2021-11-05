from flask import Flask, request, jsonify, session
from flask_mysqldb import MySQL, MySQLdb
import re
import requests
import json

app = Flask(__name__)


app.config['SECRET_KEY'] = 'g5df4v83asdas34r8t10j6sa'
app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD']= 'your_password'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_DB'] = 'mysql'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql= MySQL(app)

@app.route('/')

def home():
    return "<h1> Home Page </h1>"

# @app.route('/db')
# def db():
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM T WHERE 1")
#     rv = cur.fetchall()
#     return str(rv)
#     #return jsonify("OK")
    
@app.route('/register', methods= ['POST'])
def register():
    cur= mysql.connection.cursor()
    username= request.form.get('username').lower()
    password= request.form.get('password')
    email= request.form.get('email').lower()
    
    cur_db= mysql.connection.cursor()
    query= "SELECT * FROM userDB WHERE 1"
    cur_db.execute(query)
    db= cur_db.fetchall()
    
    for i in range(len(db)):
        if username in db[i]["username"]:
            return f"Username {username} is already registered"
        
    for i in range(len(db)):
        if email in db[i]["email"]:
            return f"email {email} is already registered"
    if len(password)<=6:
        return "Password too weak! Minimum password character length: 7"
    
    if username=="" and email=="":
        return "Both username and email cannot be Null"
        
    else:
        query= f'INSERT INTO userDB (username, password, email) VALUES ("{username}", "{password}","{email}");'
        cur.execute(query)
        rv= cur.fetchall()
        mysql.connection.commit()
        if username!="":
            return f'new user= {username}'
        if email!="":
            return f'new user= {email}'
    

@app.route('/login', methods= ['GET', 'POST'])
def login():
    cur = mysql.connection.cursor()
    username= ""
    email= ""
    if request.form.get('username') is not None:
        username= request.form.get('username').lower() 
    if request.form.get('email') is not None:
        email= request.form.get('email').lower() 
    if email is "":
        query = f"SELECT `password` FROM `userDB` WHERE username= '{username}';"
    elif username is "":
        query = f"SELECT `password` FROM `userDB` WHERE email= '{email}';"
    print(query)
    cur.execute(query)
    ret = cur.fetchall()
    # print(rv)
    if ret[0]['password'] == request.form.get('password'):                #rv is a tuple and inside of that is a dictionary
        if username!="":
            session["user"]= username 
        if email!="":
            session["email"]= email
        return (f'Password accepted, logged in as {session["user"]}')
    else:
        return 'Wrong password'
    
@app.route('/update/email', methods= ['GET', 'POST'])
def update_email():
    cur= mysql.connection.cursor()
    username= ""
    email= ""
    if request.form.get("username") is not None:
        username= request.form.get('username')
    if request.form.get("email") is not None:
        email= request.form.get('email')
    if "user" in session or "email" in session:
        print(f'Logged in as {session["user"]}')
        new_email= request.form.get('new email')
        print("new_email")
        cur_db= mysql.connection.cursor()
        query= "SELECT * FROM userDB WHERE 1"
        cur_db.execute(query)
        db= cur_db.fetchall()
        for i in range(len(db)):
            if new_email in db[i]["email"]:
                return f"Cannot update email as {new_email} is already registered, choose a different one!"
        if username!="":
            query= f'UPDATE userDB SET email="{new_email}" WHERE username= "{username}"'
        if email!="":
            query= f'UPDATE userDB SET email="{new_email}" WHERE email= "{email}"'
        cur.execute(query)
        mysql.connection.commit()
        return f'updated email to {new_email}'
    else:
        return f'Please log in first'     
    
@app.route('/moviesearch', methods= ['GET', 'POST'])
def moviesearch():
    if "user" in session:
        title= request.form.get('title')
        OMDB_API_KEY= "3d501d8e"
        url= f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t="{title}"'  
        req= requests.get(url= url)
        # print(req.json())
        # print(req.text)
        return f'logged in as {session["user"]} \n\n {req.text}'
    else:
        return f'Please log in first'    
    
@app.route('/addmovie', methods= ['GET', 'POST'])
def addmovie():
    try:
        if "user" in session or "email" in session:
            title= request.form.get('title')
            if title is not None:
                OMDB_API_KEY= "3d501d8e"
                url= f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t="{title}"'  
                req= requests.get(url= url)
                
                if req.json()['Response']== "False":
                    return "Movie not found"
                
                details= req.text
                print("session active")
                if "user" in session:
                    added_by= session["user"]
                elif "email" in session:
                    added_by= ["email"]
                    
                cur= mysql.connection.cursor()
                
                #Take the whole database========================================================
                db_query= f'SELECT * FROM movies'
                cur.execute(db_query)
                db= cur.fetchall()
                # print(db[0]) 
                # print(type(db[0]))
                #===============================================================================
                #Replacing single quotation in movie title if present, with ''==================
                pattern= re.findall(r'''("Title":)(["](\w*\s*[']*)*["])''', details)
                details_replaced= re.sub(r"'",r"''",details[0:(9+len(pattern[0][1]))]) + details[(9+len(pattern[0][1])):] 
                
                for i in range(len(db)):
                    if str(details)==db[i]['Details']: #While matching with details from database, use details variable before the replacement of single quotation
                        namelist= db[i]['Added By'].split(",")   #Turning the comma separated string into list of names in column `Added By`
                        print(f'Namelist= {namelist}')
                        if session["user"] not in namelist:
                            added_by= db[i]['Added By']+','+session["user"]
                            print(f'Added by people: {added_by}')
                            query= f'''UPDATE `movies` SET `Added By`="{added_by}" WHERE Details='{details_replaced}';'''
                            cur= mysql.connection.cursor()
                            cur.execute(query)
                            mysql.connection.commit()
                            return f'logged in as {session["user"]} \n\n Added new movie: Details= {details}'
                        elif session["user"] in namelist:
                            return f'Movie already added'
                        
                query= f'''INSERT INTO movies (`Details`, `Added By`) VALUES ('{details_replaced}',"{added_by}");'''
                cur= mysql.connection.cursor()
                cur.execute(query)
                mysql.connection.commit()
                return f'logged in as {session["user"]} \n\n Added new movie: Details= {details}'
            else:
                return "Enter a movie Title to search"
        
        else:
            return f'Please log in first' 
    except:
        return f'Please search a valid movie'
    
@app.route('/movieslist', methods= ['GET','POST'])
def movieslist():
    if "user" in session:
        username= request.form.get("username")
        print(username)
        print(session["user"])
        if username is not None:
            if session["user"] == username.lower():
                cur= mysql.connection.cursor()
                key1= r'%,'+session["user"]+r',%'
                key2= r'%,'+ session["user"]
                query= f'''SELECT * FROM movies WHERE (movies.`Added By` LIKE '{key1}') OR (movies.`Added By` LIKE '{session["user"]}') OR (movies.`Added By` LIKE '{key2}') OR (movies.`Added By` LIKE '{session["user"]},%');'''
                print(query)
                cur.execute(query)
                movies= cur.fetchall()
                movielist= []
                for i in range(len(movies)):
                    movielist.append(f'''Movie ID= {movies[i]['movieID']}, Movie Title= {json.loads(movies[i]['Details'])['Title']}''')
                return f'logged in as {session["user"]} \n\n List of movies:\n{str(movielist)}'
        else:
            return "Enter your username"
    else:
        return "Please login first"

@app.route('/deletemovie', methods= ['GET', 'POST'])
def deletemovie():
    try:
        movieID= request.form.get('movieID')
        cur= mysql.connection.cursor()
        query= f'SELECT `Added By` FROM `movies` WHERE movieID= {movieID}'
        cur.execute(query)
        added_by= cur.fetchall()[0]['Added By'].split(",") #({'Added By': 'nakkhatra54,nakkhatra002,nakkhatra003'},) is a tuple and inside is a dictionary, then we turn it into a list by comma delimiter
        if "user" in session and movieID is not None:
            if session["user"] in added_by:
                if len(added_by)>1:
                    added_by= list(filter(lambda x: x!= session["user"], added_by)) #filter with a lambda function inside returns a filter object, then we convert it into a list and then convert the list back to string for SQL query
                    added_by = ",".join(added_by)
                    print(added_by)
                    query= f'''UPDATE `movies` SET `Added By`="{added_by}" WHERE movieID= {movieID};'''
                    cur.execute(query)
                    mysql.connection.commit()
                    return f'Deleted movie from database'
                else:
                    query= f'DELETE FROM movies WHERE movieID={movieID};'
                    cur= mysql.connection.cursor()
                    cur.execute(query)
                    mysql.connection.commit()
                    return f'Deleted movie from database'
            else:
                return "Enter a valid Movie ID"
    except:
        return "Enter a valid Movie ID"
    
@app.route('/logout', methods= ['GET', 'POST'])
def logout():
    if "user" in session:
        session.clear()
        return "Logged out of account"
        
if __name__== '__main__':
    app.run(debug=True, port= 8000)