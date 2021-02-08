from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# Kullanıcı Giriş Decorator'ı  BUNU 1 KERE YAZABİLİRİZ KULLANICILARIN GÖRMESİNİ İSTEMEDİĞİMİZ ŞEYLERİ BÖYLECE HALLEDERİZ
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):  
        if "logged_in" in session:    # yani sessionda loggedin varmı ona bakıo demekki giriş yapılmış 
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim:",validators=[validators.length(min=4,max=35)])
    username = StringField("Kullanıcı Adı:",validators=[validators.length(min=3,max=25)])
    email = StringField("Eposta:",validators=[validators.email(message="Lütfen Geçerli Bir E-mail Adreis Giriniz")])
    password = PasswordField("Parolanız:",validators=[
        validators.DataRequired(message="Lütfen Bir Parola Belirleyiniz"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")

#Kullanıcı Login Form
class LoginForm(Form):
    username = StringField("Kullanıcı Adınız :")
    password = PasswordField("Parolanız:")
app = Flask(__name__)
app.secret_key="unlemtab"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "unlemtab"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select *From articles"
    result = cursor.execute(sorgu)

    if result >0:
        articles = fetchall()
        return render_template("articles.html",articles = articles) #makale varsa gösterir yoksa boş döner
    else:
        return render_template("articles.html")

#kayıt olma
@app.route("/register",methods =["GET","POST"])
def register():
    form = RegisterForm(request.form)
    

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert Into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz","succes")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)



#giriş yapma
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method =="POST":
        username = form.username.data
        password_entered = form.password.data
        sorgu = "Select * From users where username = %s"
        cursor = mysql.connection.cursor()
        result = cursor.execute(sorgu,(username,))

        if result >0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
               flash("Başarıyla Giriş Yaptınız...","success")

               session["logged_in"] = True
               session["username"] = username

               return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz...","danger")
                return redirect(url_for("login")) 

        else:
           flash("Böyle bir kullanıcı bulunmuyor...","danger")
           return redirect(url_for("login"))

    
    return render_template("login.html",form = form)


    return render_template("login.html")

#çıkış yapma işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
    flash("Başarıyla Çıkış Yapıldı,","succes")


@app.route("/projects")
def projects():
    return render_template("projects.html")
   


@app.route("/dashboard")
@login_required #dashboardı izinli yapıyoruz
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))  #giriş yapanın ismi

    if result >0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")


#makale ekleme 
@app.route("/addarticle",methods =["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data 

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()
        cursor.close()

        flash("Makale Başarıyla Eklendi")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html")

















if __name__ == "__main__":
    app.run(debug=True)

#oguzun pc
#deneme1
