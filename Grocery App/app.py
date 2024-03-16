from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, base64, io
import matplotlib.pyplot as plt
from flask import make_response, Response

app = Flask(__name__)
plt.switch_backend('Agg') 
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'grocery_store.db')

db = SQLAlchemy()
db.init_app(app)
app.app_context().push()    
usrname = ""

def update_name(nm,flag=0):
    global usrname
    if flag == 1:
        usrname = ""
    else:
        usrname += nm 
    return

class Manager_login(db.Model):
    __tablename__ = 'manager_login'
    manager_user_name = db.Column(db.String, nullable = False, primary_key = True)
    manager_password = db.Column(db.String, nullable = False)

class User_login(db.Model):
    __tablename__ = 'user_login'
    user_name = db.Column(db.String, nullable = False, primary_key = True)
    user_password = db.Column(db.String, nullable = False)

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    category_name = db.Column(db.String, nullable = False, unique = True)
    category_image = db.Column(db.BLOB)

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, autoincrement = True, primary_key = True)
    product_name = db.Column(db.String, nullable = False, unique = True)
    product_unit = db.Column(db.String, nullable = False)
    product_price = db.Column(db.Integer, nullable = False)
    product_availability = db.Column(db.Integer, nullable = False)
    product_image = db.Column(db.BLOB)
    product_category = db.Column(db.String,db.ForeignKey('category.category_name'))

item_dict = {}

@app.route('/')
def home():
    update_name("",1)
    return render_template('login.html')

@app.route('/sign_in/<category>', methods = ["GET","POST"])
def sign_in(category):
    if request.method == "GET":
        if category == "manager":
            head = "Manager Login"
            return render_template('sign_in.html', head = head, ur="manager")
        elif category == "user":
            head = "User Login"
            return render_template('sign_in.html', head = head, ur="user")
        
    elif request.method == "POST":
        if category == "manager":
            head = "Manager Login"
            iname = request.form["iname"]
            ipass = request.form["ipass"]
            manager = Manager_login.query.filter_by(manager_user_name = iname).first()
            flag = 0
            if manager != None:
                if ipass == manager.manager_password:
                        flag = 1
            
            if flag == 0:
                warn = "Invalid Username/Password"
                return render_template('sign_in.html', head = head, warn = warn, ur = "manager")
            else:
                update_name(iname)
                return manager_dashboard()
            
        elif category == "user":
            head = "User Login"
            iname = request.form["iname"]
            ipass = request.form["ipass"]
            user = User_login.query.filter_by(user_name = iname).first()
            flag = 0
            if user != None:
                if ipass == user.user_password:
                    flag = 1

            if flag == 0:
                warn = "Invalid Username/Password"
                return render_template('sign_in.html', head = head, warn = warn, ur = "user")
            else:
                update_name(iname)
                return user_dashboard()
            
@app.route('/sign_up/<category>', methods = ["GET","POST"])
def sign_up(category):
    if request.method == "GET":
        if category == "manager":
            head = "Manager : New User Sign-Up"
            return render_template('sign_up.html', head = head, ur="manager")
        elif category == "user":
            head = "User : New User Sign-Up"
            return render_template('sign_up.html', head = head, ur="user")
    
    elif request.method == "POST":
        if category == "manager":
            head = "Manager - New User Sign-Up"
            iname = request.form["iname"]
            ipass = request.form["ipass"]
            manager = Manager_login.query.filter_by(manager_user_name = iname).first()
            flag = 0
            if manager != None:
                warn = "User Name Already Exists"
                return render_template('sign_up.html', head = head, warn = warn, ur = "manager")
            else:
                new_manager = Manager_login(manager_user_name = iname, manager_password = ipass)
                db.session.add(new_manager)
                db.session.commit()
                return redirect(url_for("sign_in", category = "manager"))
            
        elif category == "user":
            head = "User - New User Sign-Up"
            iname = request.form["iname"]
            ipass = request.form["ipass"]
            user = User_login.query.filter_by(user_name = iname).first()
            flag = 0
            if user != None:
                warn = "User Name Already Exists"
                return render_template('sign_up.html', head = head, warn = warn, ur = "user")
            else:
                new_user = User_login(user_name = iname, user_password = ipass)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for("sign_in", category = "user"))
            
def manager_dashboard():
    cat = Category.query.all()
    img_tags = []
    prd = []
    for i in cat:
        base64_image = base64.b64encode(i.category_image).decode('utf-8')
        img_tag = f'<img src="data:image/png;base64,{base64_image}" class="logo" alt="Image">'
        img_tags.append(img_tag)
        tmp = []
        prdt = Product.query.filter_by(product_category = i.category_name).all()
        for j in prdt:
            if j.product_name == "b''":
                prim=""
            else:
                base64_imagepr = base64.b64encode(j.product_image).decode('utf-8')
                prim = f'<img src="data:image/png;base64,{base64_imagepr}" class="plogo" alt="Image">'
            tmp.append([j.product_name,prim])
        prd.append(tmp)
    
    result_dict = {key: [img_tags[idx], prd[idx]] for idx, key in enumerate(cat)}
    return render_template("manager_dashboard.html", name = usrname, rows=result_dict)

@app.route("/manager/category/create", methods = ["GET","POST"])
def category_create():
    if request.method=="GET":
        return render_template("category.html",cr=1, name = usrname)
    elif request.method=="POST":
        catname = request.form["catname"]
        catimg = request.files["catimg"]
        
        con1 = os.path.splitext(catimg.filename)[1] in [".png",".jpeg",".jpg",""]
        catlis = [i.category_name for i in Category.query.all()]
        con2 = catname not in catlis
        if con1 and con2 :
            if os.path.splitext(catimg.filename)[1]=="":
                static_folder = os.path.join(app.root_path, 'static')
                file_path = os.path.join(static_folder, "no_image.jpg")
                if os.path.exists(file_path):
                    catimg = open(file_path,"rb")
            cat = Category(category_name=catname,category_image=catimg.read())
            db.session.add(cat)
            db.session.commit()
            return manager_dashboard()
        else:
            err1,err2="",""
            if con1 == False:
                err1 = "Uploaded Image Filetype Not Supported."
            if con2 == False:
                err2 = "Category Name Already Exists."
            err = err2+" "+err1
            return render_template("category.html",err=err,cat=catname,cr=1, name = usrname)

@app.route("/manager/<category>/edit", methods = ["GET","POST"])
def category_edit(category):
    if request.method=="GET":
        return render_template("category.html",cat=category, name = usrname)
    elif request.method=="POST":
        catname = request.form["catname"]
        catimg = request.files["catimg"]
        
        con1 = os.path.splitext(catimg.filename)[1] in [".png",".jpeg",".jpg",""]
        catlis = [i.category_name for i in Category.query.all()]
        catlis.remove(category)
        con2 = catname not in catlis
        if con1 and con2:
            cat = Category.query.filter_by(category_name = category).first()
            cat.category_name = catname
            if os.path.splitext(catimg.filename)[1] != "":
                cat.category_image = catimg.read()
            db.session.commit()
            return manager_dashboard()
        else:
            err1,err2="",""
            if con1 == False:
                err1 = "Uploaded Image Filetype Not Supported."
            if con2 == False:
                err2 = "Category Name Already Exists."
            err = err2+""+err1
            return render_template("category.html",err=err,cat=catname, name = usrname)
        
@app.route("/manager/<category>/delete",methods = ["GET","POST"])
def category_delete(category):
    if request.method=="GET":
        msg="Are You Sure To Delete This Entire Category? All Information And Products \
            Associated With This Category Will Be Deleted!!!"
        return render_template("delete.html",msg=msg,cat=category, name = usrname)
    elif request.method=="POST":
        prd = Product.query.filter_by(product_category = category).all()
        cat = Category.query.filter_by(category_name = category).first()
        for i in prd:
            db.session.delete(i)
        db.session.delete(cat)
        db.session.commit()
        return manager_dashboard()

@app.route("/manager/<category>/product/create", methods = ["GET","POST"])
def product_create(category):
    if request.method=="GET":
        prd = Product(product_name="",product_unit="",product_price="",
                          product_availability="",product_category="")
        return render_template("product.html",cr=1,cat = category,prd=prd, name = usrname)
    elif request.method=="POST":
        prdname = request.form["prdname"]
        prdunit = request.form["prdunit"]
        prdprice = request.form["prdprice"]
        prdavl = request.form["prdavl"]
        prdimg = request.files["prdimg"]

        con1 = os.path.splitext(prdimg.filename)[1] in [".png",".jpeg",".jpg",""]
        prdlis = [i.product_name for i in Product.query.filter_by(product_category = category).all()]
        con2 = prdname not in prdlis
        if con1 and con2 :
            if os.path.splitext(prdimg.filename)[1]=="":
                static_folder = os.path.join(app.root_path, 'static')
                file_path = os.path.join(static_folder, "no_image.jpg")
                if os.path.exists(file_path):
                    prdimg = open(file_path,"rb")
            prd = Product(product_name=prdname,product_unit=prdunit,product_price=prdprice,
                          product_availability=prdavl,product_image=prdimg.read(),product_category=category)
            db.session.add(prd)
            db.session.commit()
            return manager_dashboard()
        else:
            err1,err2="",""
            if con1 == False:
                err1 = "Uploaded Image Filetype Not Supported."
            if con2 == False:
                err2 = "Product Name Already Exists."
            err = err2+" "+err1
            return render_template("product.html",err=err,prd=prdname,prdunit=prdunit,prdprice=prdprice,
                                   prdavl=prdavl,cat = category,cr=1, name = usrname)

@app.route("/manager/<product>/view")    
def product_view(product):
    if request.method=="GET":
        prd = Product.query.filter_by(product_name = product).first()
        return render_template("product_view.html",prd=prd, name = usrname)
    
@app.route("/manager/<category>/<product>/edit", methods = ["GET","POST"])    
def product_edit(category,product):
    if request.method=="GET":
        prd = Product.query.filter_by(product_name = product).first()
        return render_template("product.html",prd=prd,cat=category, name = usrname)
    elif request.method=="POST":
        prdname = request.form["prdname"]
        prdunit = request.form["prdunit"]
        prdprice = request.form["prdprice"]
        prdavl = request.form["prdavl"]
        prdimg = request.files["prdimg"]
        
        con1 = os.path.splitext(prdimg.filename)[1] in [".png",".jpeg",".jpg",""]
        prdlis = [i.product_name for i in Product.query.all()]
        prdlis.remove(product)
        con2 = prdname not in prdlis
        prd = Product.query.filter_by(product_name = product).first()
        if con1 and con2:
            prd.product_name = prdname
            prd.product_unit = prdunit
            prd.product_price = prdprice
            prd.product_availability = prdavl
            if os.path.splitext(prdimg.filename)[1] != "":
                prd.product_image = prdimg.read()
            db.session.commit()
            return redirect(url_for("product_view",product=product))
        else:
            err1,err2="",""
            if con1 == False:
                err1 = "Uploaded Image Filetype Not Supported."
            if con2 == False:
                err2 = "Product Name Already Exists."
            err = err2+""+err1
            return render_template("product.html",err=err,cat=category,prd=prd, name = usrname)

@app.route("/manager/<category>/<product>/delete",methods = ["GET","POST"])
def product_delete(category,product):
    if request.method=="GET":
        msg="Are you sure to delete this product? All information regarding to this product will be lost!!!"
        return render_template("delete.html",cr=1,prd=product,msg=msg,cat=category, name = usrname)
    elif request.method=="POST":
        prd = Product.query.filter_by(product_name = product).first()
        db.session.delete(prd)
        db.session.commit()
        return manager_dashboard()
    
@app.route("/manager/summary")
def summary():
    cat = Category.query.all()
    res={}
    for i in cat:
        temp = []
        prd = Product.query.filter_by(product_category = i.category_name).all()
        name,count,price = [],[],[]
        for j in prd:
            name.append(j.product_name)
            count.append(j.product_availability)
            price.append(j.product_price)
        
        plt.figure()
        plt.bar(name, price)
        plt.xlabel('Products')
        plt.ylabel('Price')
        plt.title('Price of Products')
        image_stream = io.BytesIO()
        plt.savefig(image_stream, format='png')
        image_stream.seek(0)

        bargraph = base64.b64encode(image_stream.read()).decode('utf-8')
        plt.close()

        img_tag = f'<img src="data:image/png;base64,{bargraph}" class="bar" alt="Image">'
        temp.append(img_tag)

        plt.clf()

        plt.figure()
        plt.pie(count, labels=name, autopct='%1.1f%%')
        plt.title('Product Availabitity')

        image_stream = io.BytesIO()
        plt.savefig(image_stream, format='png')
        image_stream.seek(0)

        piegraph = base64.b64encode(image_stream.read()).decode('utf-8')

        plt.close()

        img_tag = f'<img src="data:image/png;base64,{piegraph}" class="pie" alt="Image">'
        temp.append(img_tag)
        res[i.category_name] = temp

    return render_template("summary.html",data=res, name = usrname)

@app.route("/manager/category_back")
def category_back():
    return manager_dashboard()

def user_dashboard(msg="",filt=["",""]):
    img_tags = []
    prd = []
    
    if filt[1] == "category":
        cat = Category.query.filter_by(category_name = filt[0]).all()
    else:
        cat = Category.query.all()
        
    for i in cat:
        base64_image = base64.b64encode(i.category_image).decode('utf-8')
        img_tag = f'<img src="data:image/png;base64,{base64_image}" class="logo" alt="Image">'
        img_tags.append(img_tag)
        tmp = []
        if filt[1] == "product":
                prdt = Product.query.filter_by(product_category = i.category_name, product_name = filt[0]).all()
        else:
            prdt = Product.query.filter_by(product_category = i.category_name).all()
        for j in prdt:
            if j.product_name == "b''":
                prim=""
            else:
                base64_imagepr = base64.b64encode(j.product_image).decode('utf-8')
                prim = f'<img src="data:image/png;base64,{base64_imagepr}" class="plogo" alt="Image">'
            tmp.append([j.product_name,prim,j.product_price,j.product_unit,j.product_availability])
        prd.append(tmp)
    
    result_dict = {key: [img_tags[idx], prd[idx]] for idx, key in enumerate(cat)}
    return render_template("user_dashboard.html", rows=result_dict,msg=msg, name = usrname)

@app.route("/user/product_add",methods=["GET","POST"])
def product_add():
    if request.method == "GET":
        return user_dashboard()
    elif request.method=="POST":
        items = request.form.getlist("items")
        for i in items:
            val = float(request.form[i])            
            if i in item_dict.keys():
                item_dict[i] += val
            else: 
                item_dict[i] = val
        
        msg = "Products Added to Cart Succesfully"
        return user_dashboard(msg)

@app.route("/user/product_filter",methods=["GET","POST"])
def product_filter(): 
    if request.method=="POST":
        qstr = request.form["filter"]
        qch = request.form["choice"]

        return user_dashboard(filt=[qstr.capitalize(),qch])

def product_summary():
    result=[]
    total = 0
    for i in item_dict:
        if item_dict[i] == 0:
            continue
        else:
            temp = []
            prd = Product.query.filter_by(product_name = i).first()
            temp.append(prd.product_category)
            temp.append(prd.product_name)
            temp.append(item_dict[i])
            temp.append(prd.product_price)
            temp.append(prd.product_unit)
            cur_amt = item_dict[i]*prd.product_price
            total += cur_amt
            temp.append(cur_amt)
            temp.append(prd.product_availability)
            result.append(temp)
    return render_template("product_cart.html",res=result,total=total, name = usrname)
    

@app.route("/user/product_cart",methods=["GET","POST"])        
def product_cart():
    if request.method=="GET":
        return product_summary()
    elif request.method=="POST":
        global item_dict
        for i in item_dict:
            val = float(request.form[i])
            item_dict[i] = val
        return product_summary()

@app.route("/user/purchase",methods=["POST"])
def purchase():
    if request.method=="POST":
        for i in item_dict:
            prd = Product.query.filter_by(product_name = i).first()
            prd.product_availability -= item_dict[i]

        item_dict.clear()
        return render_template("success.html", name = usrname) 


if __name__ == '__main__':
    app.run(debug=True)
    