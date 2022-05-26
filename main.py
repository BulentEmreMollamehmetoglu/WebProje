from sys import flags
from flask import Flask,render_template,flash,redirect,url_for,logging,request
from flask import session
from flask.templating import render_template_string
from flask_mysqldb import MySQL
from sqlalchemy import false
from wtforms import Form,validators,TextAreaField,PasswordField,StringField
from passlib.hash import sha256_crypt
from functools import wraps
# from werkzeug.utils import secure_filename
from wtforms import IntegerField
from functools import wraps
from flask import g, request, redirect, url_for

app = Flask(__name__)

app.secret_key="erawebsite" #Flash mesajı işlemini yapabilmemiz için secret key belirtmemiz gerekirmiş (Ben neden olduğunu anlamadım şahsen)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "hobu"
app.config["MYSQL_CURSORCLASS"] = "DictCursor" #DictionaryCursor

mysql = MySQL(app)

#Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function

#Burası şuan kullanılmıyor
def mail_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "checkmail" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen emailinizi girin","danger")
            return redirect(url_for("login"))
    return decorated_function


@app.route('/register') #Burası sadece register sayfasını döndüren bir fonksiyondur
def register():
    return render_template('register.html')


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/") #Anasayfa
def index():
    return render_template("index.html")

@app.route("/announcements") #duyurular
def announcement():
    return render_template("announcements.html")

class UserRegisterForm(Form):
    name = StringField("Ad",validators=[validators.DataRequired()])
    surname = StringField("Soyad",validators=[validators.DataRequired()])
    nickname = StringField("Kullanıcı Adı",validators=[validators.Length(min=2,max=25),validators.DataRequired()]) #veya validators.input_required() da kullanabilirsin
    email = StringField("Mail Adresi",validators=[validators.Length(min=2,max=25),validators.DataRequired()])
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")
    major = StringField("Bölüm",validators=[validators.DataRequired()])
    university = StringField("Üniversite",validators=[validators.DataRequired()])
    phone_number = StringField("Telefon Numarası",validators=[validators.DataRequired()])
    city = StringField("Şehir",validators=[validators.DataRequired()])
    birthday_year = StringField("Doğum Tarihi",validators=[validators.DataRequired()])

@app.route("/userregister",methods=["GET","POST"])
def user_register():
    form = UserRegisterForm(request.form)
    if request.method == "POST" and form.validate():
        # name = request.form.get('name')
        # surname = request.form.get('surname')
        # nickname = request.form.get('nickname')
        # email = request.form.get('email')
        # password = sha256_crypt.encrypt(request.form.get('password'))
        # major = request.form.get('major')
        # university = request.form.get('university')
        # phone_number=request.form.get('phone_number')
        # city=request.form.get('city')
        # birthday_year=request.form.get('birthday_year')
        
        name = form.name.data
        surname = form.surname.data
        nickname = form.nickname.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        major = form.major.data
        university = form.university.data
        phone_number = form.phone_number.data
        city = form.city.data
        birthday_year = form.birthday_year.data
        
        
        

        cursor = mysql.connection.cursor()#Veritabanı üzerinde gerekli işlemleri yapabilmek için bir cursor oluşturduk

        query = "INSERT into kullanicilar(name,surname,nickname,email,password,major,university,phone_number,city,birthday_year) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(query,(name,surname,nickname,email,password,major,university,phone_number,city,birthday_year)) #gönderdiğimiz değerler demet şeklinde dikkat et!
        
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla kayıt oldunuz!","success") #Hemen bir sonraki request işleminde bu flash mesajını yayınlayabilmiş olacağız
        return redirect(url_for("index"))
    

    return render_template("userregister.html",form=form)

class LoginForm(Form):
    username = StringField("Ad",validators=[validators.DataRequired()])
    password = password = PasswordField("Parola")

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()

        query = "SELECT * FROM kullanicilar where nickname=%s "
        result = cursor.execute(query,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password,real_password):
                flash("Başarıyla giriş yapıldı. Hoşgeldiniz","success")
                session["logged_in"] = True #session anahtar değeri
                session["username"] = username #session username
                session["id"] = data["id"] #session username
                return redirect(url_for("index"))
            else:
                flash("Bilgierinizi yanlış girdiniz","danger")
        else:
            flash("Böyle bir kullanıcı bulunmuyor","danger")
            return redirect(url_for("index"))

    return render_template("login.html",form=form) #Burası sadece login sayfasını döndüren bir fonksiyondur

#Şifremi Unuttum Bölümü için Mail Kontrolü
@app.route("/sifreyenile",methods=["GET","POST"])
def sifreyenile():
    if request.method == "GET":
        return render_template("sifreyenile.html")
    else:
        email = request.form['email']
        newpassword= request.form['newpassword']
        confirm = request.form['newconfirm']
        
        cursor2 = mysql.connection.cursor()
        query2 = "SELECT * FROM kullanicilar WHERE email = %s"
        cursor2.execute(query2,(email,)) 
        data = cursor2.fetchone()
        real_password = data["password"]
        if sha256_crypt.verify(newpassword,real_password):
             flash("Yeni şifreniz öncekiyle aynı olamaz...","danger")
             return redirect(url_for("sifreyenile"))
        if newpassword == confirm:
            newpassword1 = sha256_crypt.encrypt(newpassword)            
            cursor = mysql.connection.cursor()
            query = "UPDATE kullanicilar SET password = %s WHERE email = %s"
            result = cursor.execute(query,(newpassword1,email))
            if result>0:
                flash("Şifreniz başarıyla güncellendi","success")
                mysql.connection.commit()
                return redirect(url_for("login"))
        else:
            flash("Hatalı Eşleşme","danger")
            return redirect(url_for("sifreyenile"))


#logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yapıldı","info")
    return redirect(url_for("index"))

#Kullanıcı Profil Bilgileri
@app.route("/profile/<string:id>",methods=["GET","POST"])
@login_required
def profile(id):
    if request.method =="GET":
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM kullanicilar WHERE nickname = %s and id=%s"
        result = cursor.execute(query,(session["username"],id))
        # print(result2)
        if result>0:
            data = cursor.fetchone()
            # print(data)
            return render_template("profile.html",user=data)
    else:
        newname = request.form['name']
        newsurname= request.form['surname']
        newnickname = request.form['nickname']
        newemail = request.form['email']
        newpassword = sha256_crypt.encrypt(request.form["password"])
        newmajor = request.form['major']
        newuniversity = request.form['university']
        newphone_number = request.form['phone_number']
        newcity= request.form['city']
        newbirthday_year = request.form['birthday_year']
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE kullanicilar SET name = %s, surname = %s, nickname = %s, email = %s, password = %s, major = %s, university = %s, phone_number = %s, city = %s, birthday_year = %s WHERE id = %s"
        result = cursor.execute(sorgu,(newname,newsurname,newnickname,newemail,newpassword,newmajor,newuniversity,newphone_number,newcity,newbirthday_year,id))
        mysql.connection.commit()
        if result > 0:
            flash("Kullanıcı başarılı bir şekilde güncellendi","success")
            return redirect(url_for("index"))
        else:
            flash("Bir hata ile karşılaşıldı. Lütfen tekrar deneyiniz.","danger")
            return redirect(url_for("index"))
    
@app.route("/joinevent",methods=["GET","POST"])
@login_required    
def events():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM etkinlikler"
    result = cursor.execute(query)
    if result == 0:
        cursor.close()
        flash("Henüz bir etkinlik bulunmamaktadır","danger")
        return redirect(url_for("index"))
    else:
        events = cursor.fetchall()
        cursor.close()
        return render_template("events.html",events=events)

#Giriş Yapılmadan Etkinlikleri Görebilecek Fakat Görüntüleyemeyecek   
@app.route("/showevents",methods=["GET","POST"]) 
def showevents_withoutlogin():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM etkinlikler"
    result = cursor.execute(query)
    if result == 0:
        cursor.close()
        flash("Henüz bir etkinlik bulunmamaktadır","danger")
        return redirect(url_for("index"))
    else:
        events = cursor.fetchall()
        cursor.close()
        return render_template("showevents_withoutlogin.html",events=events)

    
#Etkinlikleri Gösterme
@app.route("/showevent/<string:id>",methods=["GET","POST"])
@login_required
def showevent(id):
    cursor = mysql.connection.cursor()
    cursor2 = mysql.connection.cursor()
    
    query = "SELECT * FROM etkinlikler WHERE id=%s"
    cursor.execute(query,(id,))
    
    query2 = "SELECT * FROM etkinlikkatilimci WHERE etkinlik_id=%s and katilimci_id=%s"
    result2 = cursor2.execute(query2,(id,session["id"]))
    data2 = cursor2.fetchone() 
    
    # print(result2)
    # print(data2)
    if (data2 == None): #Veri yoksa
        session["same_id"] = False
        
    if result2>0:#Veri varsa
        session["same_id"] = data2["id"] 

    data = cursor.fetchone()

    
    return render_template("showevent.html",event=data)


#Etkinlik'e Başvurma
@app.route("/etkinlikbasvur/<string:id>")   
@login_required
def etkinlikbasvur(id): #event id'si gelecek
    cursor = mysql.connection.cursor()
    query = "INSERT into etkinlikkatilimci(etkinlik_id,katilimci_id) VALUES(%s,%s)"
    result = cursor.execute(query,(id,session["id"])) 
    if result>0:
        flash("Başvuru işlemi başarıyla gerçekleştirildi","success")
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("index"))
    else:
        flash("Başvuru işlemi esnasında bir hata oluştu","danger")
        return redirect(url_for("index"))

#Başvuru iptali
@app.route("/basvuruiptal/<string:id>")   
@login_required
def basvuruiptal(id):
    cursor = mysql.connection.cursor()
    query = "DELETE FROM etkinlikkatilimci where etkinlik_id=%s and katilimci_id=%s"
    cursor.execute(query,(id,session["id"]))
    mysql.connection.commit()
    cursor.close()
    flash("Başvuru iptal edildi","info")
    return redirect(url_for("index"))

#Sertifika Gösterme
@app.route("/sertifikalar/<string:id>",methods=["GET","POST"])
@login_required
def sertifikalar(id):
    cursor = mysql.connection.cursor()
    query = "SELECT name,surname FROM kullanicilar WHERE id=%s" #Sertifika için ad ve soyad
    cursor.execute(query,(id,))
    data = cursor.fetchone()
    
    cursor2 = mysql.connection.cursor()
    query2 = "SELECT etkinlik_id FROM etkinlikkatilimci WHERE katilimci_id=%s" #Birden çok etkinlik gelebilir
    cursor2.execute(query2,(id,))
    data2 = cursor2.fetchall()
    
    cursor3 = mysql.connection.cursor()
    query3 = "SELECT id,event_company,event_name,event_time FROM etkinlikler WHERE id=%s" #Sertifika için şirket adı,etkinlik adı , etkinlik tarihi Buranın id'si etkinlik katilimci tablosundan gelmeli
        
    liste = list()
    for i in range(0,len(data2)):
        # print(i)#0,1
        # print(data2[i]["etkinlik_id"])#1,3
        cursor3.execute(query3,(data2[i]["etkinlik_id"],))
        data3 = cursor3.fetchall()
        liste.append(data3[0])
    
    cursor4 = mysql.connection.cursor()
    query4 = "SELECT COUNT(etkinlik_id) as sayi FROM etkinlikkatilimci WHERE katilimci_id = %s"
    cursor4.execute(query4,(session["id"],))
    data4 = cursor4.fetchone();

    return render_template("sertifika.html",adsoyad=data,listeler=liste,sertifikasayi=data4)


@app.route("/sertifikagoruntule/<string:id>/<string:event_id>",methods=["GET","POST"])
@login_required
def sertifikagoruntule(id,event_id):
    cursor = mysql.connection.cursor()
    query = "SELECT name,surname FROM kullanicilar WHERE id=%s"
    cursor.execute(query,(id,))
    data = cursor.fetchone()

    cursor3 = mysql.connection.cursor()
    query3 = "SELECT event_company,event_name,event_time,event_photo,event_speakers FROM etkinlikler WHERE id=%s"
    cursor3.execute(query3,(event_id,))
    data3 = cursor3.fetchone()
    
    return render_template("sertifikagoruntule.html",adsoyad=data,eventNames=data3)

@app.route("/companies")
def sirketler():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM firma"
    result = cursor.execute(query)
    if result>0:
        data = cursor.fetchall()
        return render_template("sirketler.html",sirketler=data)
    else:
        flash("Henüz bir şirket bulunmuyor","danger")
        return redirect(url_for("sirketler"))

@app.route("/sirketgoster/<string:id>")
def sirketgoster(id):
    cursor = mysql.connection.cursor()
    
    query = "SELECT * FROM firma WHERE company_id=%s"
    cursor.execute(query,(id,))

    data = cursor.fetchone()
    return render_template("sirketgoruntule.html",sirket=data)

if __name__ == '__main__':
    app.run(debug=True)