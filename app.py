from flask import Flask, request, render_template, redirect, url_for, session
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os
from flask_admin.form import ImageUploadField
from flask_admin import AdminIndexView
from flask import redirect, url_for, session, request
from flask_admin.menu import MenuLink
from wtforms.fields import SelectField

# Crear la app Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','Rr_123456')
database_url = os.getenv('DATABASE_URL')

if not database_url:
    # Fallback local
    database_url = 'postgresql://postgres:Talon1528@localhost/mitienda'

# Conexión con PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static','uploads')

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'sslmode': 'require'}
}

# Inicializar SQLAlchemy directamente
db = SQLAlchemy(app)

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

# Vista protegida para cada modelo
class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('admin_logged_in')

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))
    
    def render (self, template, **kwargs):
        kwargs['logout_button'] = Markup('<a class="btn btn-danger" href="/admin/logout">Cerrar sesión</a>')
        return super().render(template, **kwargs)
    
class ProductoAdmin(ModelView):
    form_extra_fields = {
        'imagen': ImageUploadField('Imagen del producto',
                                   base_path=os.path.join(os.getcwd(), 'static', 'uploads'),
                                   relative_path='uploads/',
                                   url_relative_path='static/uploads/'
                                   )
    }
    form_overrides = {
        'id_categoria': SelectField
    }
    form_columns = ['nombre', 'descripcion', 'imagen', 'precio','id_categoria']
    # Sobrescribimos el tipo de campo
    form_overrides = {
        'id_categoria': SelectField
    }
    # Configuramos el comportamiento del SelectField
    form_args = {
        'id_categoria': {
        'coerce': int,
        'label': 'Categoría'
        }
    }
    # Llenamos las opciones para el campo select (crear)
    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.id_categoria.choices = [(c.id_categoria, c.nom_categoria) for c
        in Categoria.query.all()]
        return form
    # Llenamos las opciones para el campo select (editar)
    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.id_categoria.choices = [(c.id_categoria, c.nom_categoria) for c
        in Categoria.query.all()]
        return form

# Modelos
class Categoria(db.Model):
    __tablename__ = 'categorias'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nom_categoria = db.Column(db.String(100), nullable=False)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(200))
    precio = db.Column(db.Float, nullable=False)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categorias.id_categoria'), nullable=False)
    categoria = db.relationship('Categoria', backref='productos')

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_ud_usuario = db.Column(db.Integer, primary_key=True)
    nom_usuario = db.Column(db.String(50), nullable=False)
    ape_usuario = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)  # usuario de login
    password = db.Column(db.String(128), nullable=False)

# Flask-Admin
admin = Admin(app, name='Panel Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_view(ModelView(Usuario, db.session))
admin.add_view(ModelView(Categoria, db.session))
admin.add_view(ProductoAdmin(Producto, db.session))
admin.add_link(MenuLink(name='Cerrar sesion', category='', url='/admin/logout'))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/inicio/")
def inicio():
    return render_template("index.html")

@app.route('/productos')
def productos():
    return render_template('plantilla1.html')

@app.route('/servicios')
def servicios():
    return render_template('plantilla2.html')

@app.route('/ventas')
def ventas():
    productos = Producto.query.all()
    return render_template('ventas.html', productos=productos)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Usuario.query.filter_by(nom_usuario=username, password=password).first()

        if user:
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            error = 'Usuario o contraseña incorrectos'
    
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)