from flask import *
import sqlite3
import uuid
from functools import wraps
import base64
import os
from flask_apscheduler import APScheduler
from datetime import datetime
import logging
from datetime import timedelta
app = Flask(__name__)
scheduler = APScheduler()
app.secret_key = 'your-secret-key'  # Replace with a strong, unique key
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the folder if it doesn't exist
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Print the absolute path for debugging
print(f"Absolute UPLOAD_FOLDER path: {os.path.abspath(UPLOAD_FOLDER)}")
#gamelord
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
class GlobalVar:
    def __init__(self,value):
        self.value=value
global_var=GlobalVar('First')

review_filter_global=GlobalVar('ReviewSQL')

class User:
    def __init__(self,username,email,password,user_type):
        self.username=username
        self.email=email
        self.password=password
        self.buyer_address=''
        self.store_region=''
        self.card_info=''
        self.company_name=''
        self.publisher_name=''
        self.user_type=user_type
        self.account_status='active'

class Game_publish_request:
      def __init__(self,game_name,game_genre,estimated_release_year,basic_description):
   
            self.request_id=uuid.uuid4().hex
            self.username=''
            self.game_name=game_name
            self.game_genre=game_genre
            self.estimated_release_year=estimated_release_year
            self.basic_description=basic_description
            self.status='Pending'  

class Games_List:
    def __init__(self,game_name,game_genre,game_description,base_price):
        self.game_name=game_name
        self.game_genre=game_genre
        self.game_description=game_description
        self.base_price=base_price



          

def connect_db():
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS USERS(
        username TEXT PRIMARY KEY UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        buyer_address TEXT,
        store_region TEXT CHECK(store_region IN('NA','LA','EU','ASI','')),
        card_info INT,
        company_name TEXT,
        publisher_name TEXT CHECK(publisher_name IN('bandai_namco','playstation_publishing','xbox_game_studios','square_enix','sega','self','')),
        user_type TEXT CHECK(user_type IN('buyer','developer','admin')) NOT NULL,
        account_status TEXT CHECK(account_status IN('active','terminated')) NOT NULL
    )
""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS WALLET_BALANCE (
            username TEXT PRIMARY KEY,
            balance REAL DEFAULT 0,
            FOREIGN KEY (username) REFERENCES USERS(username)
        )
    """)

    c.execute("SELECT * FROM USERS WHERE username = 'LordGaben'")
    existing_user = c.fetchone()

    if existing_user is None:
        # Insert the user with the password for the first time
        c.execute("""
            INSERT INTO USERS (username, email, password, user_type, account_status)
            VALUES ('LordGaben', 'newell@steampowered.com', '123456', 'admin', 'active')
        """)
        db.commit()


    c.execute("""
    INSERT INTO WALLET_BALANCE (username, balance)
    SELECT ?, ?
    WHERE NOT EXISTS (
        SELECT 1 FROM WALLET_BALANCE WHERE username = ?
    )
""", ('LordGaben', 0, 'LordGaben'))
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS GAME_PUBLISH_REQUEST(
        request_id TEXT, 
        username TEXT,
        game_name TEXT, 
        game_genre TEXT, 
        estimated_release_year INT(4), 
        basic_description TEXT, 
        status TEXT CHECK(status IN ('Pending', 'Accepted', 'Rejected','Completed'))
    )
""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS SENT_FRIEND_REQUEST (
        username_from TEXT,
        username_to TEXT,
        request_status TEXT CHECK (request_status IN ('Pending', 'Accepted', 'Rejected')),
        FOREIGN KEY (username_from) REFERENCES USERS(username),
        FOREIGN KEY (username_to) REFERENCES USERS(username)
    )
""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS FRIENDS (
        username_me TEXT,
        username_friendswith TEXT,
        
        FOREIGN KEY (username_me) REFERENCES USERS(username),
        FOREIGN KEY (username_friendswith) REFERENCES USERS(username)
    )
""")
    #CREATIING GAME LIST TABLE
    c.execute("""
            CREATE TABLE IF NOT EXISTS GAME_LIST(
              game_name TEXT UNIQUE NOT NULL,
              game_genre TEXT NOT NULL,
              game_description TEXT NOT NULL,
              base_price INT NOT NULL
              CHECK(base_price between 0 AND 120),
              game_status TEXT CHECK(game_status in ('Active','Delisted')) NOT NULL,
              dev_username TEXT NOT NULL,
              rating_yes INT NOT NULL,
              rating_no INT NOT NULL, 
              copies_sold INT NOT NULL,
              revenue_generated INT NOT NULL,
              img_path_logo TEXT NOT NULL,
              img_path_ss1 TEXT NOT NULL,
              img_path_ss2 TEXT NOT NULL,
              game_file_path TEXT NOT NULL,
              sale_status TEXT CHECK(sale_status in(True,False)),
              actual_price INT NOT NULL CHECK(actual_price between 0 AND 120),
              sale_end_time DATETIME,
              sale_percentage INT CHECK(sale_percentage between 0 AND 90),
              release_year INT NOT NULL,
              FOREIGN KEY (dev_username) REFERENCES USERS(username)


              )

""")
    c.execute("""
                CREATE TABLE IF NOT EXISTS WISHLIST(
              username TEXT NOT NULL,
              game_name TEXT NOT NULL,
              FOREIGN KEY (username) REFERENCES USERS(username),
              FOREIGN KEY (game_name) REFERENCES game_list(game_name)

              )
        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS CART_SYSTEM (
              username TEXT NOT NULL,
              game_name TEXT NOT NULL,
              was_it_on_sale TEXT check(was_it_on_sale in(True,False)),
              FOREIGN KEY (username) REFERENCES USERS(username),
              FOREIGN KEY (game_name) REFERENCES game_list(game_name)

              )
            """)
    c.execute(""" 
            CREATE TABLE IF NOT EXISTS OWNED_GAMES(
              
              username TEXT NOT NULL,
              game_name TEXT NOT NULL,
              amount_paid INT NOT NULL,
              purchase_type TEXT NOT NULL CHECK (purchase_type in ('Digital','Product_key')),
              posted_review TEXT NOT NULL CHECK (posted_review in ('yes','no')),
              FOREIGN KEY (username) REFERENCES USERS(username),
              FOREIGN KEY (game_name) REFERENCES game_list(game_name)
              )

        """)
    c.execute("""
            CREATE TABLE IF NOT EXISTS WALLET_CODE(
                wallet_key TEXT NOT NULL,
                amount INT NOT NULL,
                status TEXT CHECK (status in('ACTIVE','USED'))
            )          
              """
        
        
    )
    c.execute("""
            CREATE TABLE IF NOT EXISTS GAME_KEY(
                game_key TEXT NOT NULL,
                game_name TEXT NOT NULL,
                status TEXT CHECK (status in('ACTIVE','USED')),
                FOREIGN KEY (game_name) REFERENCES game_list(game_name)
            )          
              """
        
        
    )
    c.execute("""
            CREATE TABLE IF NOT EXISTS Reviews(
                game_name TEXT NOT NULL,
                username TEXT NOT NULL,
              
                review TEXT NOT NULL,
              rating TEXT NOT NULL CHECK(rating IN('yes','no')),
                FOREIGN KEY (username) REFERENCES USERS(username),
                FOREIGN KEY (game_name) REFERENCES game_list(game_name)
            )          
              """
        
        
    )
    

    

    db.commit()
    c.connection.close()


@app.route('/')
def index():
    connect_db()

    if 'user_type' in session:
        if session['user_type'] == 'buyer':
            return redirect(url_for('buyer_dashboard'))
        elif session['user_type'] == 'developer':
            return redirect(url_for('developer_dashboard'))
        elif session['user_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
    # If no session, redirect to login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    
    if request.method == 'GET':
        return render_template('index.html')
    

    if request.is_json:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        print(f"Username: {username}, Password: {password}")

      
        c.execute("SELECT username, user_type,store_region FROM USERS WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        c.execute("SELECT username, user_type FROM USERS WHERE username = ? AND password = ? AND account_status='active'", (username, password))
        user_active_check = c.fetchone()
        print("Fetched user:", user)

        if user:
            if user_active_check:
                session.permanent = True
        
                session['username'] = user[0]
                session['user_type'] = user[1]
                session['store_region']=user[2]
            else:
                 return jsonify({"error": "Account Terminated due to fraudent activities"}), 401    

            return jsonify({
                "success": True,
                "redirect_url": url_for(f"{user[1]}_dashboard") 
            }), 200  
        else:
         
            return jsonify({"error": "Invalid credentials"}), 401  
   
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login')) 


@app.route('/current_user')
def current_user():
    if 'user_type' in session:
        username = session['username']
        

        db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
        c = db.cursor()
        

        c.execute("SELECT email FROM USERS WHERE username = ?", (username,))
        user_data = c.fetchone()
        
        
        if user_data:
            return jsonify({"username": username, "user_type": session['user_type'], "email": user_data[0]})
        else:
            return jsonify({"error": "User data not found"})
        
    else:
        return jsonify({"error": "Not logged in"})

@app.route('/newacc', methods=['GET'])
def new_account_buyer():

    return render_template('newacc.html')  

@app.route('/forgotpass', methods=['GET'])
def forgot_pass():

    return render_template('forgotpass.html')



@app.route('/forgot_password', methods=['POST'])
def forgot_password():

    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')

  
    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400  

   
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute("SELECT email FROM USERS WHERE email = ?", (email,))
    user = c.fetchone()


    if not user:
        return jsonify({"error": "Email not found."}), 404  

    c.execute("UPDATE USERS SET password = ? WHERE email = ?", (new_password, email))
    db.commit()
    db.close()


    return jsonify({"success": "Password reset successfully."}), 200 






@app.route('/devacc', methods=['GET'])
def new_account_developer():
 
    return render_template('devacc.html') 



@app.route('/create_buyer', methods=['POST'])
def create_buyer():
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()
   
    if not request.is_json:
        return jsonify({"error": "Invalid request. Please send data as JSON."}), 400

   
    data = request.json
    username = data.get('user_name')
    email = data.get('email')
    password = data.get('password')
    buyer_address = data.get('buyer_address')
    store_region = data.get('store_region')
    card_info = data.get('card_info')
    print(username,email)
    
    if not (username and email and password and buyer_address and store_region and card_info):
        return jsonify({"error": "All fields are required."}), 400


    new_buyer = User(username, email, password, "buyer")
    new_buyer.buyer_address = buyer_address
    new_buyer.store_region = store_region
    new_buyer.card_info = card_info
    print(new_buyer.username)
  

    user_check=checkUser()  
    print(user_check)  
    if len(user_check)!=0:
        return jsonify({"error": "Username or email already exists."}), 400

    else: 
        c.execute("""
            INSERT INTO USERS (username, email, password, buyer_address, store_region, card_info, user_type,account_status)
            VALUES (?, ?, ?, ?, ?, ?, ?,?)
        """, (new_buyer.username, new_buyer.email, new_buyer.password, 
                new_buyer.buyer_address, new_buyer.store_region, new_buyer.card_info, 
                new_buyer.user_type,'active'))
        c.execute("""
    INSERT INTO WALLET_BALANCE VALUES (?,?)
                  """,(new_buyer.username,0))
        db.commit()
        db.close()

    # If successful, return success response
        return jsonify({"success": "Buyer account created successfully.", "redirect_url": url_for('index')}), 200



@app.route('/create_developer', methods=['POST'])
def create_developer():
    db=sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c=db.cursor()

    if not request.is_json:
        return jsonify({"error": "Invalid request. Please send data as JSON."}), 400

   
    data = request.json
    username = data.get('user_name')
    email = data.get('email')
    password = data.get('password')
    company_name = data.get('company_name')
    publisher_name = data.get('publisher_name')
   
    print(username,email)
   
    if not (username and email and password and company_name and publisher_name ):
        return jsonify({"error": "All fields are required."}), 400

    new_developer = User(username, email, password, "developer")
    new_developer.company_name = company_name
    new_developer.publisher_name = publisher_name
    
    print(new_developer.username)
  

    user_check=checkUser()  
    print(user_check)  
    if len(user_check)!=0:
        return jsonify({"error": "Username or email already exists."}), 400

 
    else: 
        c.execute("""
            INSERT INTO USERS (username, email, password, company_name, publisher_name, user_type,account_status)
            VALUES (?, ?, ?, ?, ?, ?,?)
        """, (new_developer.username, new_developer.email, new_developer.password, 
                new_developer.company_name, new_developer.publisher_name, 
                new_developer.user_type,'active'))
        c.execute("""
    INSERT INTO WALLET_BALANCE VALUES (?,?)
                  """,(new_developer.username,0))
        db.commit()
        db.close()

        return jsonify({"success": "Developer account created successfully.", "redirect_url": url_for('index')}), 200






@app.route('/checkUser', methods=['GET'])
def checkUser():
    data = request.json
    username = data.get('user_name')
    email = data.get('email')
    c = sqlite3.connect("bashpos_--definitely--_secured_database.db").cursor()
    c.execute("SELECT * FROM USERS WHERE username = ? OR email = ?", (username, email))
    data=c.fetchall()
    return data




def login_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'user_type' not in session:
                return redirect(url_for('login'))  
            if session['user_type'] != role:
                return "Unauthorized Access", 403  
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


@app.route('/dev_dashboard', methods=['GET','POST'])
@login_required('developer')
def developer_dashboard():
    connect_db()
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT username,company_name,publisher_name,email FROM USERS WHERE user_type ='developer' and username=?",(session['username'],))
        dev_data = c.fetchone()
        dev_username=dev_data[0]
        company_name=dev_data[1]
        publisher_name=dev_data[2]
        dev_email=dev_data[3]
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)

        c.execute("SELECT game_name, status from GAME_PUBLISH_REQUEST WHERE username=?",(session['username'],))
        game_req_data = c.fetchall()
        c.execute("SELECT game_name,game_status, base_price,copies_sold,sale_status,actual_price,sale_end_time FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        game_list_data=c.fetchall()
        print(game_list_data)
        c.execute("SELECT COUNT(*) FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        no_of_total_games=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM GAME_LIST WHERE dev_username=? AND game_status='Active'",(dev_username,))
        no_of_games_active=c.fetchone()[0]
        c.execute("SELECT SUM(copies_sold) FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        no_of_total__games_sold=c.fetchone()[0]
        delisted_games_count=no_of_total_games-no_of_games_active
        c.execute("SELECT game_name, copies_sold, revenue_generated FROM GAME_LIST WHERE dev_username=?",(dev_username,))
        revenue_data=c.fetchall()
        c.execute("SELECT game_key, game_name FROM GAME_KEY WHERE STATUS='ACTIVE'")
        game_key_active=c.fetchall()

       
    return render_template('dev_dashboard.html',dev_username=dev_username, balance=balance,company_name=company_name,
                           publisher_name=publisher_name.upper(),dev_email=dev_email,game_req_data=game_req_data,game_list_data=game_list_data,
                           no_of_total__games_sold=no_of_total__games_sold, no_of_total_games= no_of_total_games,no_of_games_active=no_of_games_active,
                           delisted_games_count=delisted_games_count,revenue_data=revenue_data,game_key_active=game_key_active)


@app.route('/GenerateGameKey', methods=['GET','POST'])

def generate_game_key():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        req_json = request.json
        game_name = req_json.get('game_name')
        no_of_keys = req_json.get('numberofkeys')
        for i in range(no_of_keys):
            game_key = uuid.uuid4().hex
            c.execute("INSERT INTO game_key values (?, ?, ?)", (game_key, game_name, "ACTIVE"))
            db.commit()
        return jsonify({'ok':True})

@app.route('/buyer_dashboard', methods=['GET', 'POST'])
@login_required('buyer')
def buyer_dashboard():
    connect_db()
    buyer_username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()

        # Fetch wallet balance
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?", (buyer_username,))
        balance = round(c.fetchone()[0],2)


        # Fetch the three most recently added games
        c.execute("""
            SELECT game_name, game_genre, img_path_ss1
            FROM GAME_LIST
            WHERE game_status = 'Active'
            ORDER BY rowid DESC
            LIMIT 3
        """)
        featured_games = c.fetchall()

        for i in range(len(featured_games)):
            featured_games[i]=list(featured_games[i])
        print(featured_games)
        
        c.execute("SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage FROM game_list where game_status='Active'")
        game_list = c.fetchall()
        
        
        for i in range(len(game_list)):
            game_list[i] = list(game_list[i])
        print(game_list)
        
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*.8,2)
                game_list[i] [4] = round(game_list[i] [4]*.8,2)
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [2] =round(game_list[i] [2]*1,2)
                game_list[i] [4] =round(game_list[i] [4]*1,2)
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*.9,2)
                game_list[i] [4] = round(game_list[i] [4]*.9,2)
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                game_list[i] [4] = round(game_list[i] [4]*1.1,2)
            print(game_list)
        print(global_var.value)
        c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_value=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        cart_value=c.fetchone()[0]
        if cart_value==0:
            cart_status='0'
        else:
            cart_status='1'    

        c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
        wishlist_user=c.fetchall()
        print(wishlist_user)
        for i in range(len(wishlist_user)):
                wishlist_user[i] = list(wishlist_user[i])
        if session['store_region'] == 'ASI':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'NA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'LA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'EU':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2)     
    # Pass the data to the storefront template
    return render_template(
        'buyer_storefront.html',
        buyer_username=buyer_username,
        balance=balance,
        featured_games=featured_games, 
        game_list = game_list, wishlist_value=wishlist_value,wishlist_user=wishlist_user,cart_value=cart_value,cart_status=cart_status )
@app.route('/AddMonitorWallet', methods=['GET', 'POST'])
@login_required('buyer')
def wallet_purchase():
    connect_db()
    buyer_username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()

        # Fetch wallet balance
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?", (buyer_username,))
        balance = c.fetchone()[0]
        c.execute("SELECT game_name,amount_paid,purchase_type from OWNED_GAMES where username=?",(buyer_username,))
        game_info=c.fetchall()
        return render_template('wallet&purchase.html', buyer_username = buyer_username, balance = balance,game_info=game_info)

@app.route('/AddtoWishlist',methods=['GET','POST'])
def Add_to_Wishlist():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            req_json=request.json
            game_name=req_json.get('game_name')
            username=session['username']
            #check if game already in user wishlist

            c.execute("SELECT * FROM WISHLIST WHERE game_name=? and username=?",(game_name,username))
            already_check=c.fetchall()
            #check if game already in owned games

            c.execute("SELECT * FROM OWNED_GAMES WHERE game_name=? and username=?",(game_name,username))
            ALREADY_OWNED=c.fetchall()
            
            
            print('wishlisted',already_check)
            if len(already_check)>0:
                return jsonify({"message": f"{game_name} cannot be added as it already exists in your wishlist."})
            elif len(ALREADY_OWNED)>0:
                return jsonify({"message": f"{game_name} cannot be added as you already own it."})
            else:
                c.execute("INSERT INTO WISHLIST VALUES (?,?)",(username,game_name))
                db.commit()
                return jsonify({"message": f"{game_name} added to wishlist!"})


@app.route('/AddtoCart',methods=['GET','POST'])
def Add_to_Cart():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            req_json=request.json
            game_name=req_json.get('game_name')
            username=session['username']
            was_it_on_sale=req_json.get('was_it_on_sale')
            #check if game already in user wishlist

            c.execute("SELECT * FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,username))
            
            already_check=c.fetchall()
            print('wishlisted',already_check)
            if len(already_check)>0:
                return jsonify({"message": f"{game_name} cannot be added as it already in your cart."})
            else:
                c.execute("INSERT INTO CART_SYSTEM VALUES (?,?,?)",(username,game_name,was_it_on_sale))
                db.commit()
            return jsonify({"message": f"{game_name} added to cart!"})

@app.route('/ViewCart',methods=['GET','POST'])
def View_Cart():
    buyer_username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT c.game_name, c.was_it_on_sale, g.base_price, g.actual_price, g.sale_status,g.img_path_logo,g.sale_percentage FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(buyer_username,))
        
        game_list=c.fetchall()
        for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
               game_list[i] [2] = round(game_list[i] [2]*.8,2)
               game_list[i] [3] = round(game_list[i] [3]*.8,2)
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*1,2)
                game_list[i] [3] =round(game_list[i] [3]*1,2)
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [2] =round(game_list[i] [2]*.9,2)
                game_list[i] [3] = round(game_list[i] [3]*.9,2)
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                game_list[i] [3] = round(game_list[i] [3]*1.1,2)
        total_price=0
        for i in game_list:
            total_price+=i[3]
        c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_value=c.fetchone()[0]    
        c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
        wishlist_user=c.fetchall()
        print(wishlist_user)
        for i in range(len(wishlist_user)):
                wishlist_user[i] = list(wishlist_user[i])
        if session['store_region'] == 'ASI':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'NA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'LA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'EU':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2) 
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        cart_value=c.fetchone()[0]
        return render_template('cart.html',buyer_username=buyer_username,balance=balance,game_list=game_list,total_price=total_price,store_region=session['store_region'],
                               wishlist_user=wishlist_user,wishlist_value=wishlist_value,cart_value=cart_value)

@app.route('/RemoveFromCart',methods=['GET','POST'])
def RemoveFromCart():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            req_json=request.json
            username=req_json.get('username')
            game_name=req_json.get('game_name')
            c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,username))
            db.commit()
            c.execute("SELECT c.game_name, c.was_it_on_sale, g.base_price, g.actual_price, g.sale_status,g.img_path_logo,g.sale_percentage FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(username,))
        
            game_list=c.fetchall()
            c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
            balance = round(c.fetchone()[0],2)
            for i in range(len(game_list)):
                    game_list[i] = list(game_list[i])
            if session['store_region'] == 'ASI':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*.8,2)
                    game_list[i] [3] = round(game_list[i] [3]*.8,2)
                print(game_list)
                
            elif session['store_region'] == 'NA':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*1,2)
                    game_list[i] [3] =round(game_list[i] [3]*1,2)
                print(game_list)
                
            elif session['store_region'] == 'LA':
                for i in range(len(game_list)):
                    game_list[i] [2] =round(game_list[i] [2]*.9,2)
                    game_list[i] [3] = round(game_list[i] [3]*.9,2)
                print(game_list)
                
            elif session['store_region'] == 'EU':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                    game_list[i] [3] = round(game_list[i] [3]*1.1,2)
        c.execute("SELECT * FROM CART_SYSTEM WHERE username=?",(username,))
        is_empty=c.fetchall()
        if len(is_empty)>0:
            return jsonify({"success": True,"empty_check":False, "message": "Game removed from cart"})
        else:
            return jsonify({"success": True,"empty_check":True, "message": "Game removed from cart"})

@app.route('/RemoveFromWishlist',methods=['GET','POST'])
def RemoveFromWishlist():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor() 
            req_json=request.json
            username=session['username']
            game_name=req_json.get('game_name')
            c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,username))
            db.commit()
            return jsonify({"success": True, "message": "Game removed from wishlist"})

@app.route('/PayUsingWallet',methods=['GET','POST'])
def Pay_Using_Wallet():
     buyer_username=session['username']
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT c.game_name, g.actual_price FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(buyer_username,))
        
        game_list=c.fetchall()
        for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
               game_list[i] [1] = round(game_list[i] [1]*.8,2)
             
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*1,2)
             
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [1] =round(game_list[i] [1]*.9,2)
            
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*1.1,2)
 
        total_price=0
        for i in game_list:
            total_price+=i[1]
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        if balance<total_price:
             return jsonify({"success": False, "message": "Insufficient funds"})
        else:
            for i in game_list:
                game_name=i[0]
                paying_amount=round(i[1],2)
                c.execute("SELECT dev_username FROM GAME_LIST WHERE game_name=?",(game_name,))
                dev_username=c.fetchone()[0]
                if len(c.execute("select * from reviews WHERE game_name=? and username=?",(game_name,session['username'])).fetchall())==0:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','no'))
                else:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','yes'))
                dev_cut=round(paying_amount*0.9,2)
                admin_cut=round(paying_amount*0.1,2)
                c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold+1, revenue_generated=revenue_generated+? where game_name=?",(dev_cut,game_name))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance-? where username=?",(paying_amount,buyer_username))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(dev_cut,dev_username))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(admin_cut,'LordGaben'))
                c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,buyer_username))
                c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,buyer_username))
                db.commit()
            return jsonify({"success": True, "message": "All games  bought successfully"})

@app.route('/PayUsingCard' , methods=['GET','POST'])
def Pay_With_Card():
    buyer_username=session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT c.game_name, g.actual_price FROM CART_SYSTEM c INNER JOIN GAME_LIST g on g.game_name=c.game_name where c.username=? and g.game_status='Active'",(buyer_username,))
        
        game_list=c.fetchall()
        for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
        if session['store_region'] == 'ASI':
            for i in range(len(game_list)):
               game_list[i] [1] = round(game_list[i] [1]*.8,2)
             
            print(game_list)
            
        elif session['store_region'] == 'NA':
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*1,2)
             
            print(game_list)
            
        elif session['store_region'] == 'LA':
            for i in range(len(game_list)):
                game_list[i] [1] =round(game_list[i] [1]*.9,2)
            
            print(game_list)
            
        elif session['store_region'] == 'EU':
            for i in range(len(game_list)):
                game_list[i] [1] = round(game_list[i] [1]*1.1,2)
 
        total_price=0
        for i in game_list:
            total_price+=i[1]
        req_json=request.json
        card_info=req_json.get('card_info')
        c.execute("SELECT CARD_INFO from USERS WHERE username=?",(buyer_username,))
        card_fetched=c.fetchone()[0]
        
        if int(card_info)!=card_fetched:
            return jsonify({'success': False})
        else:
            for i in game_list:
                game_name=i[0]
                paying_amount=round(i[1],2)
                c.execute("SELECT dev_username FROM GAME_LIST WHERE game_name=?",(game_name,))
                dev_username=c.fetchone()[0]
                if len(c.execute("select * from reviews WHERE game_name=? and username=?",(game_name,session['username'])).fetchall())==0:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','no'))
                else:
                    c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,paying_amount,'Digital','yes'))
                dev_cut=round(paying_amount*0.9,2)
                admin_cut=round(paying_amount*0.1,2)
                c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold+1, revenue_generated=revenue_generated+? where game_name=?",(dev_cut,game_name))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(dev_cut,dev_username))
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(admin_cut,'LordGaben'))
                c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,buyer_username))
                c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,buyer_username))
                db.commit()
            return jsonify({"success": True, "message": "All games  bought successfully"})






    



@app.route('/SearchFilterApi',methods=['GET','POST'])
def SearchFilter():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()

            req_json=request.json
            print(req_json)
            ordertype=req_json.get('ordertype')
            secondcondition=req_json.get('query_filter')
            sqlcommand=SearchQueryMaker(ordertype,secondcondition)
            print(sqlcommand)
            global_var.value=sqlcommand
        return ""

def SearchQueryMaker(ordertype,query_filter):
    query_filter=query_filter
    if ordertype=='game_genre':
        strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage  FROM game_list ORDER BY CASE WHEN game_genre = "+"'"+query_filter+"'"+ " THEN 1 ELSE 2 END, game_name"
        
    elif ordertype=='release_year':
        if query_filter=='ascending':
            strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage FROM game_list ORDER BY release_year ASC"

        elif query_filter=='descending':
            strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage FROM game_list ORDER BY release_year DESC"   
    elif ordertype=='actual_price':
        if query_filter=="low-to-high":
           strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage FROM game_list ORDER BY actual_price ASC"  
        elif query_filter=="high-to-low":
            strings=strings="SELECT game_name, game_genre, actual_price, img_path_logo,base_price,sale_status,sale_percentage FROM game_list ORDER BY actual_price DESC" 


             
    return strings
    

@app.route('/SearchFilterReturner',methods=['GET','POST'])
def ReturnFilter():
   
    sqlcommand=global_var.value
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute(sqlcommand)
            game_list=c.fetchall()
            for i in range(len(game_list)):
                game_list[i] = list(game_list[i])
            print(game_list)
        
            if session['store_region'] == 'ASI':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*.8,2)
                    game_list[i] [4] = round(game_list[i] [4]*.8,2)
                print(game_list)
                
            elif session['store_region'] == 'NA':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*1,2)
                    game_list[i] [4] =round(game_list[i] [4]*1,2)
                print(game_list)
                
            elif session['store_region'] == 'LA':
                for i in range(len(game_list)):
                    game_list[i] [2] =round(game_list[i] [2]*.9,2)
                    game_list[i] [4] = round(game_list[i] [4]*.9,2)
                print(game_list)
                
            elif session['store_region'] == 'EU':
                for i in range(len(game_list)):
                    game_list[i] [2] = round(game_list[i] [2]*1.1,2)
                    game_list[i] [4] = round(game_list[i] [4]*1.1,2)
                    
            return render_template('game_list_jinga.html',game_list_sort=game_list)


@app.route('/ReviewFilterApi',methods=['GET','POST'])
def ReviewFilter():
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()

            req_json=request.json
            
           
            query_type=req_json.get('query_filter')
            game_name=req_json.get('game_name')
            print(query_type)
            if query_type=='positive':
                review_filter_global.value="SELECT username,review, rating FROM REVIEWS where game_name="+"'"+ game_name+"'"+"and rating='yes'"
            elif query_type=='negative':
                review_filter_global.value="SELECT username,review, rating FROM REVIEWS where game_name="+"'"+ game_name+"'"+"and rating='no'"
            elif query_type=='all':
                review_filter_global.value="SELECT username,review, rating FROM REVIEWS where game_name="+"'"+ game_name+"'"

            
            
        return ""
@app.route('/ReviewFilterReturner',methods=['GET','POST'])
def ReturnReviewFilter():
   
    sqlcommand=review_filter_global.value
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute(sqlcommand)
            print('sqlll',sqlcommand)
            reviews_sorted=c.fetchall()
            
                    
            return render_template('review_list_jinja.html',reviews_sorted=reviews_sorted)


@app.route('/ViewGamePage/<game_name>',methods=['GET','POST'])
def View_Game_Page(game_name):
     if request.method=='GET':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("SELECT * from game_list where game_name = ?", (game_name,))
            
            game_info = c.fetchall()
            c.execute("SELECT * from owned_games where game_name = ? and username=?", (game_name,session['username']))
            game_bought=c.fetchone()
            print('bought check',game_bought)
            if game_bought==None or len(game_bought)==0:
                bought_check='0'
            else:
                bought_check='1' 
            print(bought_check)       
            for i in range(len(game_info)):
                game_info[i] = list(game_info[i])
            print(game_info)
            game_info=game_info[0]
            print(game_info)
            rating_yes=game_info[6]
            rating_no=game_info[7]
            rating=RatingCalculator(rating_yes,rating_no)
            if session['store_region'] == 'ASI':
               
                    game_info[3] = round(game_info[3]*.8,2)
                    game_info [15] = round(game_info [15]*.8,2)
                
                
            elif session['store_region'] == 'NA':
                
                    game_info [3] = round(game_info[i] [3]*1,2)
                    game_info[15] =round(game_info[i] [15]*1,2)
          
                
            elif session['store_region'] == 'LA':
              
                game_info [3] =round(game_info[3]*.9,2)
                game_info [15] = round(game_info [15]*.9,2)
               
                
            elif session['store_region'] == 'EU':
              
                    game_info [3] = round(game_info [3]*1.1,2)
                    game_info [15] = round(game_info [15]*1.1,2)
            
        
            c.execute("SELECT publisher_name from users where username = ?", (game_info[5],))
            publisher_name = c.fetchone()[0]
            buyer_username = session['username']
            c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
            balance = round(c.fetchone()[0],2)
            c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
            wishlist_value=c.fetchone()[0]
            c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
            wishlist_user=c.fetchall()
            print(wishlist_user)
            for i in range(len(wishlist_user)):
                 wishlist_user[i] = list(wishlist_user[i])
            if session['store_region'] == 'ASI':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                    wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
                print(wishlist_user)
                
            elif session['store_region'] == 'NA':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                    wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
                print(wishlist_user)
                
            elif session['store_region'] == 'LA':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                    wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
                print(wishlist_user)
                
            elif session['store_region'] == 'EU':
                for i in range(len(wishlist_user)):
                    wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                    wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2)   
            c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
            cart_value=c.fetchone()[0]
            if cart_value==0:
                cart_status='0'
            else:
                cart_status='1'   
            c.execute("SELECT username,review, rating from Reviews where game_name=?",(game_name,))
            reviews=c.fetchall()
            return render_template('game_page.html', game_info = game_info, publisher_name = publisher_name,rating=rating,
                                   buyer_username=buyer_username,balance=balance,wishlist_value=wishlist_value,
                                   wishlist_user=wishlist_user,bought_check=bought_check,cart_status=cart_status,cart_value=cart_value,reviews=reviews)
def RatingCalculator(ratings_yes,ratings_no):
    if ratings_no==0 and ratings_yes==0:
        return 'Not enough ratings'
    elif ratings_yes>0 and ratings_no==0:
        if ratings_yes>10:
            return "Overwhelmingly Positive"
        else:
            return "Very Positive"
    elif ratings_yes>0 and ratings_no>0:
        total_ratings=ratings_yes+ratings_no
        ratings_percentage=(ratings_yes/total_ratings)*100
        if ratings_percentage>=96:
            return "Overwhelmingly Positive"
        elif ratings_percentage<96 and ratings_percentage>=84:
            return "Very Positive"
        elif ratings_percentage<84 and ratings_percentage>=75:
            return "Positive"
        elif ratings_percentage<75 and ratings_percentage>=65:
            return "Mostly Positive"
        elif ratings_percentage<65 and ratings_percentage>=55:
            return "Mixed"
        elif ratings_percentage<55 and ratings_percentage>=45:
            return "Negative"
        elif ratings_percentage<45 and ratings_percentage>=35:
            return "Very Negative"
        elif ratings_percentage<35:
            return "Overwhelmingly Negative"


@app.route('/ViewMyProfile',methods=['GET','POST'])
@login_required('buyer')
def buyer_profile():
    buyer_username = session['username']
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT username,email,buyer_address,store_region,card_info, account_status FROM USERS where username=?",(session['username'],))
        buyer_details=c.fetchone()
        status=buyer_details[5].upper()
        card_info=str(buyer_details[4])
        c.execute("SELECT username_from FROM SENT_FRIEND_REQUEST where username_to=? and request_status='Pending'",(session['username'],))
        pending_requests=c.fetchall()
        c.execute("SELECT username_friendswith FROM FRIENDS where username_me=?",(session['username'],))
        my_friends=c.fetchall() 
        c.execute("SELECT COUNT(*) FROM WISHLIST w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        wishlist_value=c.fetchone()[0]
        c.execute("SELECT w.username, w.game_name, g.base_price,g.actual_price,g.sale_status FROM WISHLIST w INNER JOIN game_list g ON g.game_name=w.game_name WHERE username=?",(buyer_username,))
        wishlist_user=c.fetchall()
        print(wishlist_user)
        for i in range(len(wishlist_user)):
                wishlist_user[i] = list(wishlist_user[i])
        if session['store_region'] == 'ASI':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*.8,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.8,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'NA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1,2)
                wishlist_user[i] [3] =round(wishlist_user[i] [3]*1,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'LA':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] =round(wishlist_user[i] [2]*.9,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*.9,2)
            print(wishlist_user)
            
        elif session['store_region'] == 'EU':
            for i in range(len(wishlist_user)):
                wishlist_user[i] [2] = round(wishlist_user[i] [2]*1.1,2)
                wishlist_user[i] [3] = round(wishlist_user[i] [3]*1.1,2)  
        
        c.execute("SELECT COUNT(*) FROM CART_SYSTEM w INNER JOIN GAME_LIST g ON g.game_name=w.game_name WHERE w.username=? and g.game_status='Active'",(buyer_username,))
        cart_value=c.fetchone()[0]
        if cart_value==0:
            cart_status='0'
        else:
            cart_status='1'  
          
        c.execute("SELECT o.game_name, o.username, g.game_file_path,o.posted_review from OWNED_GAMES o INNER JOIN GAME_LIST g on g.game_name=o.game_name where o.username=?",(buyer_username,))
        owned_games=c.fetchall()
        print(owned_games)
    return render_template('Buyer_profile.html',balance=balance,buyer_username=buyer_username,buyer_data=buyer_details,account_status=status,
                           card_info=card_info,pending_requests=pending_requests,my_friends=my_friends,store_region=session['store_region'],
                           wishlist_value=wishlist_value,wishlist_user=wishlist_user,cart_status=cart_status,cart_value=cart_value,owned_games=owned_games)


@app.route('/PostReview', methods=['GET','POST'])
def Post_Review():
    buyer_username = session['username']
    if request.method=='POST':
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            req_json=request.json
            game_name=req_json.get('game_name')
            rating=req_json.get('rating')
            review=req_json.get('review')

            print('test',game_name,rating,review)
            c.execute("INSERT INTO REVIEWS values (?,?,?,?)",(game_name,buyer_username,review,rating))
            if rating=='yes':
                c.execute("UPDATE GAME_LIST SET rating_yes=rating_yes+1 where game_name=?", (game_name,))
            elif rating=='no':
                c.execute("UPDATE GAME_LIST SET rating_no=rating_no+1 where game_name=?", (game_name,))
            c.execute("UPDATE OWNED_GAMES SET posted_review='yes' where game_name=? and username=?",(game_name,buyer_username))
            db.commit()
            return jsonify({'success': True, 'message':'Review for '+game_name+' posted successfully'})

@app.route('/UpdateCreditCard', methods=['POST','GET'])
def Update_card():
    if request.method=='POST':
        buyer_username = session['username']
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            req_json=request.json
            card_number=req_json.get('card_number')
            c.execute("UPDATE USERS SET card_info=? where username=?", (card_number,buyer_username))
            db.commit()
            return jsonify({'success': True  })

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').lower()

    # Query the database for matching games
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT game_name, img_path_logo FROM game_list WHERE LOWER(game_name) LIKE ?", (f"%{query}%",))
        results = cursor.fetchall()


    
    return jsonify({
        'results': [
            {
                'name': row[0],
                'logo': url_for('static', filename=row[1])  # Converts to a full URL (e.g., "/static/uploads/elden_ring_logo.png")
            }
            for row in results
        ]
    })




@app.route('/admin_dashboard')
@login_required('admin')
def admin_dashboard():
    connect_db()
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM USERS WHERE user_type ='buyer' and account_status = 'active'")
        active_users = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM USERS WHERE user_type = 'developer'")
        developers = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM USERS WHERE user_type ='buyer' and account_status = 'terminated'")
        terminated_users = c.fetchone()[0]
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT username FROM USERS WHERE user_type ='buyer' and account_status = 'active'")
        all_users = c.fetchall()
        c.execute("SELECT username,company_name FROM USERS WHERE user_type ='developer' and account_status = 'active'")
        all_devs = c.fetchall()       
        c.execute("""
        SELECT u.username, w.balance
        FROM USERS u
        INNER JOIN WALLET_BALANCE w ON u.username = w.username
        WHERE u.user_type = 'developer';
    """)
        

        developer_earnings=c.fetchall()
        c.execute("""
        SELECT SUM(w.balance) FROM WALLET_BALANCE w INNER JOIN USERS u on 
                  u.username=w.username
    """)
        total_cash_flow=c.fetchone()[0] 

        all_requests=getRequests_admin()
        c.execute("SELECT game_name, revenue_generated FROM GAME_LIST order by revenue_generated desc")
        highest_game=c.fetchone()
        c.execute("SELECT w.username, w.balance FROM wallet_balance w INNER JOIN USERS U on u.username=w.username where user_type='developer' order by balance desc")
        highest_dev=c.fetchone()
        
        if highest_dev==None:
            highest_dev=['none',0]
        if highest_game==None:
            highest_game=['None',0]
        c.execute("SELECT wallet_key, amount FROM WALLET_CODE WHERE STATUS='ACTIVE'")
        wallet_codes_active=c.fetchall()
        print(highest_game,highest_dev)

    return render_template('admin_dashboard.html', username=session['username'], active_users=active_users, developers=developers, terminated_users=terminated_users, 
                           balance=balance,all_users=all_users,
                           developer_earnings=developer_earnings,all_devs=all_devs,all_requests=all_requests,
                           total_cash_flow=total_cash_flow, highest_game=highest_game,highest_dev=highest_dev,wallet_codes_active=wallet_codes_active)

@app.route('/generatewallet', methods=['GET','POST'])
@login_required('admin')
def generate_wallet():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        req_json = request.json
        value = req_json.get('amount')
        no_of_cards = req_json.get('numberOfCards')
        for i in range(no_of_cards):
            wallet_code = uuid.uuid4().hex
            c.execute("INSERT INTO WALLET_CODE values (?, ?, ?)", (wallet_code, value, "ACTIVE"))
            db.commit()
        return jsonify({'ok':True})

@app.route('/RedeemGiftCard', methods=['GET','POST'])
def redeem_wallet():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        req_json=request.json
        gift_card=req_json.get('gift_code')
        c.execute("SELECT * FROM WALLET_CODE WHERE wallet_key=?",(gift_card,))
        check_card=c.fetchall()
        if len(check_card)==0:
            return jsonify({'success':False, 'message':'Please enter a valid card key'})
        else:
            c.execute("SELECT * FROM WALLET_CODE WHERE wallet_key=?",(gift_card,))
            check_card=c.fetchall()[0]
            print(check_card)
            if check_card[2]=='USED':
                return jsonify({'success':False, 'message':'This card key has been used'})
            else:
                denomination=check_card[1]
               
                c.execute("UPDATE WALLET_BALANCE SET balance=balance+? WHERE username=?",(denomination,session['username'])) 
                c.execute("UPDATE WALLET_CODE SET status='USED' where wallet_key=?", (gift_card,))
                db.commit()
            return jsonify({'success':True, 'message':str(denomination)+' $ added to account successfully'})

@app.route('/ActivateProductKey', methods=['GET','POST'])
def activate_game_key():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        req_json=request.json
        product_key=req_json.get('product_key')
        c.execute("SELECT * FROM GAME_KEY WHERE game_key=?",(product_key,))
        check_product_key=c.fetchall()
        if len(check_product_key)==0:
            return jsonify({'success':False, 'message':'Please enter a valid game key'})
        else:
            c.execute("SELECT * FROM GAME_KEY WHERE game_key=?",(product_key,))
            check_product_key=c.fetchall()[0]
            if check_product_key[2]=='USED':
                return jsonify({'success':False, 'message':'This game key has been used already'})
            else:
                
                game_name=check_product_key[1]
                print(game_name)
                c.execute("SELECT * FROM OWNED_GAMES WHERE game_name=? and username=?",(game_name,session['username']))
                
                game_already_owned=c.fetchall()
                print(game_already_owned)
                if len(game_already_owned)>0:
                    return jsonify({'success':False, 'message':'You already own this game'})
                else:
                    
                    c.execute("SELECT dev_username,base_price FROM GAME_LIST WHERE game_name=?",(game_name,))
                    data=c.fetchone()
                    dev_username=data[0]
                    price=data[1]*0.85
                    if len(c.execute("select * from reviews WHERE game_name=? and username=?",(game_name,session['username'])).fetchall())==0:
                        c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,price,'Product_key','no'))
                    else:
                        c.execute("INSERT INTO OWNED_GAMES VALUES (?,?,?,?,?)",(session['username'],game_name,price,'Product_key','yes'))
                    dev_cut=round(price*0.9,2)
                    admin_cut=round(price*0.1,2)
                    c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold+1, revenue_generated=revenue_generated+? where game_name=?",(dev_cut,game_name))
                    c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(dev_cut,dev_username))
                    c.execute("UPDATE WALLET_BALANCE SET balance=balance+? where username=?",(admin_cut,'LordGaben'))
                    c.execute("DELETE FROM CART_SYSTEM WHERE game_name=? and username=?",(game_name,session['username']))
                    c.execute("DELETE FROM WISHLIST WHERE game_name=? and username=?",(game_name,session['username']))
                    c.execute("UPDATE GAME_KEY SET status='USED' where GAME_key=?", (product_key,))
                    
                    db.commit()
                return jsonify({'success':True, 'message':str(game_name)+' added to account successfully'})
        




@app.route('/get_active_buyers', methods=['GET'])
def get_active_buyers():
    with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT username FROM USERS WHERE user_type = 'buyer' AND account_status = 'active'")
        buyers = c.fetchall()  
    return jsonify(buyers)  

@app.route('/terminate_buyer', methods=['POST'])
def terminate_buyer():
    data = request.json  
    username = data.get('username')

    if username:
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE USERS SET account_status = 'terminated' WHERE username = ?", (username,))
            db.commit()
        return jsonify({"message": f"User {username} terminated successfully."})
    else:
        return jsonify({"error": "Invalid request"}), 400

@app.route('/DelistGame', methods=['POST'])
def Delist_game():
    data = request.json  
    game_name = data.get('game_name')

    if game_name:
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE GAME_LIST SET game_status = 'Delisted' WHERE game_name = ?", (game_name,))
            db.commit()
        return jsonify({"message": f"{game_name} delisted successfully."})
    else:
        return jsonify({"error": "Invalid request"}), 400
@app.route('/RefundGame', methods=['POST'])
def Refund_game():
    buyer_username=session['username']
    data = request.json  
    game_name = data.get('game_name')
    game_price=int(data.get('price'))
   
    if game_name:
        with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
            c = db.cursor()
            c.execute("UPDATE WALLET_BALANCE SET balance = balance+? WHERE username= ?", (game_price,buyer_username))
            c.execute("SELECT dev_username FROM GAME_LIST WHERE game_name=?",(game_name,))
            dev_username=c.fetchone()[0]
           
            dev_cut=round(game_price*0.9,2)
            admin_cut=round(game_price*0.1,2)
            c.execute("UPDATE GAME_LIST SET copies_sold=copies_sold-1, revenue_generated=revenue_generated-? where game_name=?",(dev_cut,game_name))
           
            c.execute("UPDATE WALLET_BALANCE SET balance=balance-? where username=?",(dev_cut,dev_username))
            c.execute("UPDATE WALLET_BALANCE SET balance=balance-? where username=?",(admin_cut,'LordGaben'))
            c.execute("DELETE FROM OWNED_GAMES where game_name=? and username=?",(game_name,buyer_username))

            db.commit()
        return jsonify({"message": f"{game_name} refunded successfully."})
    else:
        return jsonify({"error": "Invalid request"}), 400


@app.route('/SendFriendRequest', methods=['GET','POST'])
@login_required('buyer')
def Send_Friend_Request():
     if request.method == 'POST':
        db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
        c=db.cursor()
        req_json = request.json
        friend_email=req_json.get('email')
        sender_username=session['username']
        c.execute("SELECT username FROM USERS where email=? and user_type='buyer'",(friend_email,))
        friend_username=c.fetchone()
        if  friend_username==None:
            return jsonify({"success": False, "message": "This email doesn't belong to a buyer or doesn't exist"})
        else:
            friend_username=friend_username[0]   
        if friend_username==session['username']:
             return jsonify({"success": False, "message": "You cannot send a friend request to yourself"})
        print(friend_username)
        #checking if a request is pending or accepted
        c.execute("SELECT request_status FROM SENT_FRIEND_REQUEST WHERE username_from=? and username_to=? and request_status!='Rejected'",(sender_username,friend_username))
        check_duplicate=c.fetchall()
        c.execute("SELECT request_status FROM SENT_FRIEND_REQUEST WHERE username_from=? and username_to=? and request_status!='Rejected'",(friend_username,sender_username))
        check_duplicate_2=c.fetchall()
        if len(check_duplicate)!=0:
            return jsonify({"success": False, "message": "Cannot send friend request as currently a request is "+check_duplicate[0][0]})
        elif len(check_duplicate_2)!=0:
            return jsonify({"success": False, "message": "Cannot send friend request as currently a request is "+check_duplicate_2[0][0]})
        else:
            c.execute("INSERT INTO SENT_FRIEND_REQUEST VALUES (?,?,?)",(sender_username,friend_username,'Pending'))
            db.commit()
            return jsonify({"success": True, "message": "Friend Request sent succesfully"})


@app.route('/updateFriendRequest', methods=['POST'])
@login_required('buyer')
def update_FriendRequest():
 
    req_json = request.json
    friends_username = req_json.get('username_from')
    status = req_json.get('request_status')

    if not friends_username or status not in ['Accepted', 'Rejected']:
        return jsonify({"response": "Invalid request data"}), 400
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute(
        "UPDATE SENT_FRIEND_REQUEST SET request_status=? WHERE username_from=? and username_to=?",
        (status, friends_username,session['username']),
    )
    if status=='Accepted':
        c.execute("INSERT INTO FRIENDS VALUES (?,?)",(session['username'],friends_username))
        db.commit()
        c.execute("INSERT INTO FRIENDS VALUES (?,?)",(friends_username,session['username']))
    db.commit()
    return jsonify({"message": "Request updated to "+status})        


@app.route('/ViewFriendProfile/<friend_username>')
def view_friend_profile(friend_username):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT email,account_status FROM USERS WHERE username=?",(friend_username,))
        friend_data=c.fetchone()
        # Pass the friend's username to the template
        c.execute("SELECT game_name, username from OWNED_GAMES  where username=?",(friend_username,))
        friends_games=c.fetchall()
        return render_template('ViewFriendProfile.html', friendusername=friend_username,buyer_username=session['username'],balance=balance,friend_email=friend_data[0],
                               friend_account_status=friend_data[1].upper(),friends_games=friends_games)
     
@app.route('/UploadGameDataForm/<game_name>')
@login_required('developer')
def uploadgamedta_formpage(game_name):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        print(game_name)

        
        # Pass the friend's username to the template
        return render_template('upload_game_data.html',game_name=game_name,dev_username=session['username'])
     
@app.route('/ViewBuyerProfile/<buyer_username>')
def view_buyer_profile(buyer_username):
     with sqlite3.connect('bashpos_--definitely--_secured_database.db') as db:
        c = db.cursor()
        c.execute("SELECT balance FROM WALLET_BALANCE WHERE username = ?",(session['username'],))
        balance = round(c.fetchone()[0],2)
        c.execute("SELECT email,account_status FROM USERS WHERE username=?",(buyer_username,))
        buyer_data=c.fetchone()
        c.execute("SELECT game_name, username from OWNED_GAMES  where username=?",(buyer_username,))
        friends_games=c.fetchall()
        # Pass the friend's username to the template
        return render_template('ViewBuyerProfile.html', friendusername=buyer_username,username=session['username'],balance=balance,friend_email=buyer_data[0],
                               friend_account_status=buyer_data[1].upper(),friends_games=friends_games)


@app.route('/SendPublishingRequest', methods=['GET','POST'])

def Send_Publishing_Request():
    if request.method == 'POST':
        db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
        c=db.cursor()
        req_json = request.json
        Pub_request=Game_publish_request(req_json["game_name"],req_json["game_genre"],req_json["estimated_release_year"],req_json["basic_description"])
        print(Pub_request)
        game_avail_check=getPub_Req_Avail(req_json["game_name"])
        if len(game_avail_check)!=0:
            return jsonify({"success": False, "message": "Cannot send request as request for a game with the same name has already been accepted or waiting for approval"})
        else:
            c.execute("INSERT INTO GAME_PUBLISH_REQUEST VALUES(?,?,?,?,?,?,?)",
                    (Pub_request.request_id,session['username'],Pub_request.game_name,Pub_request.game_genre,
                        Pub_request.estimated_release_year,Pub_request.basic_description
                        , Pub_request.status))
            db.commit()
            db.close()
        
            return  jsonify({"success": True,"message": "Publishing request for "+req_json['game_name']+ " sent successfully"})
        

@app.route('/StartSaleRequest', methods=['GET','POST'])

def Send_Sale_Request():
    if request.method == 'POST':
        db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
        c=db.cursor()
        req_json = request.json
        print(req_json)
     
        game_name=req_json.get('game_name')
        sale_percentage_value=req_json.get('sale_percentage')
        sale_percentage=int(req_json.get('sale_percentage'))/100
       
        sale_end_date=req_json.get('sale_end_date')
        if not req_json:
            return jsonify({"success": False, "message": "Cannot send request as request for a game with the same name has already been accepted or waiting for approval"})
        else:
            c.execute("SELECT actual_price FROM GAME_LIST WHERE game_name=?",(game_name,))
            actual_price_current=c.fetchone()[0]
            new_actual_price=actual_price_current-actual_price_current*sale_percentage
            c.execute("UPDATE GAME_LIST SET actual_price=?, sale_status=?,sale_end_time=?,sale_percentage=? WHERE game_name=?",(new_actual_price,True,sale_end_date,sale_percentage_value,game_name))
            db.commit()
            db.close()
        
            return  jsonify({"success": True,"message": "Sale for "+req_json['game_name']+ " started successfully"})
        
@app.route('/uploadgamedata', methods=['GET','POST'])
def uploadgamedata():
     if request.method == 'POST':
        db=sqlite3.connect("bashpos_--definitely--_secured_database.db")
        c=db.cursor()
        req_json = request.json
        game_name=req_json.get('game_name')
        game_genre=req_json.get('game_genre')
        dev_username=req_json.get('dev_username')
        game_description=req_json.get('game_description')
        base_price=req_json.get('base_price')
        logo=req_json.get('logo')
        screenshot1=req_json.get('screenshot1')
        screenshot2=req_json.get('screenshot2')
        game_file=req_json.get('game_file')
        release_year=req_json.get('release_year')
        
        print(release_year)
        logo_data = base64.b64decode(logo)

        # Generate a safe filename for the image to find em properlyy
        logo_filename = f"{game_name.replace(' ', '_').lower()}_logo.png"
        logo_file_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        
        # Save the image to the upload folder
        with open(logo_file_path, 'wb') as f:
            f.write(logo_data)
        
        ss1_data = base64.b64decode(screenshot1)

        # Generate a safe filename for the image  to find em properlyy
        ss1_filename = f"{game_name.replace(' ', '_').lower()}_ss1.png"
        ss1_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ss1_filename)
        
        # Save the image to the upload folder
        with open(ss1_file_path, 'wb') as f:
            f.write(ss1_data)

        ss2_data = base64.b64decode(screenshot2)

        # Generate a safe filename for the image  to find em properlyy
        ss2_filename = f"{game_name.replace(' ', '_').lower()}_ss2.png"
        ss2_file_path = os.path.join(app.config['UPLOAD_FOLDER'], ss2_filename)
        
        # Save the image to the upload folder
        with open(ss2_file_path, 'wb') as f:
            f.write(ss2_data) 
        
        game_file_data = base64.b64decode(game_file)

        # Generate a safe filename for the zipped file
        game_file_filename = f"{game_name.replace(' ', '_').lower()}_file.zip"
        game_file_path = os.path.join(app.config['UPLOAD_FOLDER'], game_file_filename)
        
        # Save the files to the upload folder
        with open(game_file_path, 'wb') as f:
            f.write(game_file_data)     
        logo_file_url = f"uploads/{logo_filename}"
        ss1_file_url = f"uploads/{ss1_filename}"
        ss2_file_url = f"uploads/{ss2_filename}"
        game_file_url = f"uploads/{game_file_filename}"

 #########images send to  static/upload AND we will save the path data in DB
                 # def __init__(self,game_name,game_genre,game_description,base_price):
        game_data=Games_List(game_name,game_genre,game_description,base_price)
        c.execute("  INSERT INTO GAME_LIST VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (game_data.game_name,game_data.game_genre,
                game_data.game_description,game_data.base_price,'Active',dev_username,0,0,0,0,logo_file_url,ss1_file_url,ss2_file_url,game_file_url,False,game_data.base_price,None,None,release_year))
        db.commit()
        c.execute("UPDATE GAME_PUBLISH_REQUEST SET status = 'Completed' WHERE username = ? and game_name=?", (dev_username, game_name))
        db.commit()
        return jsonify({"message": "Data for "+game_name+" uploaded successfully"})


@app.route('/getPubReq', methods=['GET'])
def getPub_Req_Avail(game_name):
    game_name=game_name
    c = sqlite3.connect("bashpos_--definitely--_secured_database.db").cursor()
    c.execute("SELECT * FROM GAME_PUBLISH_REQUEST where game_name=? and status!='Rejected'",(game_name,))
    data=c.fetchall()
    return data


@app.route('/getRequests', methods=['GET'])
def getRequests_admin():
    c = sqlite3.connect("bashpos_--definitely--_secured_database.db").cursor()
    c.execute("SELECT * FROM GAME_PUBLISH_REQUEST where status='Pending'")
    data=c.fetchall()
    return data


@app.route('/updateRequest', methods=['POST'])
@login_required('admin')
def update_request():
 
    req_json = request.json
    request_id = req_json.get('request_id')
    status = req_json.get('status')

    if not request_id or status not in ['Accepted', 'Rejected']:
        return jsonify({"response": "Invalid request data"}), 400
    db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
    c = db.cursor()
    c.execute(
        "UPDATE GAME_PUBLISH_REQUEST SET status=? WHERE request_id=?",
        (status, request_id),
    )
    if status=='Accepted':
        c.execute("UPDATE WALLET_BALANCE SET balance=balance+1000 where username='LordGaben'")
    db.commit()
    return jsonify({"message": "Request updated to "+status})

    
@app.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        username = session['username']
        db = sqlite3.connect('bashpos_--definitely--_secured_database.db')
        c = db.cursor()

        
        c.execute("SELECT password FROM USERS WHERE username = ?", (username,))
        stored_password = c.fetchone()

        if stored_password and stored_password[0] == current_password:
            # Update the password
            print('newpass: ',new_password,username)
            c.execute("UPDATE USERS SET password = ? WHERE username = ?", (new_password, username))
            db.commit()
            db.close()

            return jsonify({"success": True, "message": "Password updated successfully!"})
        else:
            return jsonify({"success": False, "error": "Incorrect current password!"})

    return redirect(url_for('logout'))

@app.route('/check_session')
def check_session():
    if 'user' in session:
        return f"User: {session['username']}"
    else:
        return "Session has expired."


def reset_expired_sales():
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    
    db = sqlite3.connect("bashpos_--definitely--_secured_database.db")
    c = db.cursor()
  
    
    c.execute("""
        UPDATE GAME_LIST SET actual_price = base_price, sale_status = ?, sale_end_time=?,sale_percentage=? 
        WHERE sale_end_time IS NOT NULL AND sale_end_time <= ?
    """, (False, None,None,current_time))
    
    db.commit()
    db.close()
    logging.debug("reset_expired_sales function completed.")

scheduler.add_job(id='reset_sales', func=reset_expired_sales, trigger='interval', seconds=20)
scheduler.start()







if __name__=="__main__":
    app.run(debug=True, port=1097)