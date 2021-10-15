from flask import Flask, render_template,flash,redirect,url_for,session,logging,request #render_template looks for "templates" named folder
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#User login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu səhifəyə getməy üçün əvvəlcə giriş etməlisiniz!",category="danger")
            return redirect(url_for("login"))
        
    return decorated_function

#if user logged in decorator
def logged_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return redirect(url_for("index"))
            
        else:
            
            return f(*args, **kwargs)
        
    return decorated_function

#user register form
class RegisterForm(Form):
    
    name = StringField("Ad Soyad",validators=[validators.Length(min=8,max=30,message="Ad Soyad 8 ilə 30 simvol arası olmalıdır."), validators.DataRequired()])
    username = StringField("İstifadəçi adı",validators=[validators.Length(min=3,max=15,message="İstifadəçi adı 4 ilə 15 simvol arası olmalıdır."), validators.DataRequired()])
    email = StringField("Email",validators=[validators.Email(message="Bu düzgün bir e-poçt ünvanı deyil. Zəhmət olmasa bir daha cəhd edin."), validators.DataRequired()])
    password = PasswordField("Şifrə",validators=[
        validators.Length(min=8,max=30,message="Şifrə 8 ilə 30 simvol arası olmalıdır."), 
        validators.DataRequired(message="Şifrənizi daxil etməyi unutmusunuz!"),
        validators.EqualTo(fieldname="confirm",message="Şifrələr üsd-üsdə düşmür!")
        ])
    confirm = PasswordField("Şifrəni təsdiq edin")

#login form
class LoginForm(Form):
    username = StringField("İstifadəçi adı",validators=[validators.DataRequired()])
    password = PasswordField("Şifrə")

#Article form
class ArticleForm(Form):
    title = StringField("Məqalə başlığı",validators=[validators.Length(min = 2,max = 100,message="Məqalə başlığı 2 ilə 100 simvol arası olmalıdır."),validators.DataRequired()])
    content = TextAreaField("Məqalə məzmunu",validators=[validators.Length(min = 30,message="Məqalə məzmunu minumum 30 simvol olmalıdır."),validators.DataRequired()])

app =  Flask(__name__)
app.secret_key = "website"   #for flush messagin

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "website"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register",methods = ["GET","POST"])  #accept 2 request. get and post   
@logged_required
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) 
        
        cursor = mysql.connection.cursor()

        query = "INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(query,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()

        flash("Qeydiyyat prosesi uğurla tamamlandı!",category="success")

        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(query,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")
@app.route("/login",methods = ["GET","POST"])
@logged_required
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        
        username = form.username.data
        password_entred = form.password.data
        
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(query,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if sha256_crypt.verify(password_entred,real_password):
                flash("Giriş prosesi uğurla sonlandırıldı!","success")

                session["logged_in"] = True
                session["username"] = username
                

                return redirect(url_for("index"))
            else:
                flash("Parol düzgün deyil!","danger")
                return redirect(url_for("login"))


        else:
            flash("Belə bir istifadəçi tapılmadı!",category="danger")
            return redirect(url_for("login"))


    else:
        return render_template("login.html",form=form)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Çıxış edildi!",category="warning")
    return redirect(url_for("index"))


@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        
        query = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(query,(title,session["username"],content,))
        mysql.connection.commit()
        cursor.close()

        flash("Məqalə uğurla əlavə edildi",category="success")

        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form = form)

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles"
    result = cursor.execute(query)

    if result>0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")

@app.route("/article/<string:id>")
def detail(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(query,(id,))

    if result>0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        
        return render_template("article.html")

#delete article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE author = %s AND id = %s"
    result = cursor.execute(query,(session["username"],id))

    if result>0:
        query2 = "DELETE FROM articles WHERE id=%s"
        cursor.execute(query2,(id,))
        mysql.connection.commit()
        flash("Silmə prosesi uğurla tamamlndı!",category="info")
        return redirect(url_for("dashboard"))
    else:
        flash("Belə bir məqalə yoxdur və ya bunu silməy haqqınız yoxdur!",category="danger")
        return redirect(url_for("index"))

#update article
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM articles WHERE id=%s AND author=%s"
        result = cursor.execute(query,(id,session["username"]))

        if result == 0:
            flash("Belə bir məqalə yoxdur və ya bunu silməy haqqınız yoxdur!",category="danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
        
    #post request
    else:
        form = ArticleForm(request.form)
        if form.validate():

            newTitle = form.title.data
            newContent = form.content.data

            query2 = "UPDATE articles SET title=%s , content=%s WHERE id=%s"

            cursor = mysql.connection.cursor()
            cursor.execute(query2,(newTitle,newContent,id))

            mysql.connection.commit()

            flash("Məqalə uğurla güncəlləndi!","success")
            return redirect(url_for("dashboard"))
        else:
            return render_template("update.html",form=form)   

#search url
@app.route("/search",methods  = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM articles WHERE title LIKE '%" + keyword +"%'"
        result = cursor.execute(query,) #45345

        if result == 0:
            flash("Bu sözə uyğun məqalə tapılmadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)
if __name__ == '__main__':
    app.run(debug=True)