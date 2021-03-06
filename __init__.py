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
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)

    if result >0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles) #makale varsa gösterir yoksa boş döner
    else:
        return render_template("articles.html")

#detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article= article)
    else:
        return render_template("article.html")

#makale formu oluşturma işlemi
class ArticleForm(Form):
    title = StringField("Konunuz",validators=[validators.length(min = 6,max=100)])
    content = TextAreaField("Konu İçeriği",validators=[validators.length(min =10)])





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
@login_required #dashbordu izinsiz kullanmamak için bunu yapıyoruz
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))  #yine veritabanı

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
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
    return render_template("addarticle.html",form = form)


#makale güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
   if request.method == "GET":
       cursor = mysql.connection.cursor()

       sorgu = "Select * from articles where id = %s and author = %s"
       result = cursor.execute(sorgu,(id,session["username"]))

       if result == 0:
           flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
           return redirect(url_for("index"))
       else:
           article = cursor.fetchone()
           form = ArticleForm()

           form.title.data = article["title"]
           form.content.data = article["content"]
           return render_template("update.html",form = form)

   else:
       # POST REQUEST
       form = ArticleForm(request.form)

       newTitle = form.title.data
       newContent = form.content.data

       sorgu2 = "Update articles Set title = %s,content = %s where id = %s "

       cursor = mysql.connection.cursor()

       cursor.execute(sorgu2,(newTitle,newContent,id))

       mysql.connection.commit()

       flash("Makale başarıyla güncellendi","success")

       return redirect(url_for("dashboard"))

       pass

#makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    
    if result > 0:
       sorgu2 = "Delete from articles where id = %s"
       cursor.execute(sorgu2,(id,))
       mysql.connection.commit()
       return redirect(url_for("dashboard"))
    else:
        flash("Bu makaleyi silme yetkiniz yok")
        return redirect(url_for("index"))













if __name__ == "__main__":
    app.run(debug=True)

#oguzun pc
#deneme1
