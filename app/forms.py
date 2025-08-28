from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Length, Email, EqualTo, Optional, ValidationError # Added Email, EqualTo, Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed

class ToyForm(FlaskForm):
    name = StringField('Nombre del Juguete', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descripción')
    price = FloatField('Precio (A$)', validators=[DataRequired(), NumberRange(min=0.01)])
    # Categorías pregrabadas (incluye las categorías existentes en la base de datos)
    CATEGORIES = [
        ('Niña', 'Niña'),
        ('Niño', 'Niño'),
        ('Mixto', 'Mixto'),
        ('Figuras', 'Figuras'),
        ('Peluches', 'Peluches'),
        ('Juegos de Mesa', 'Juegos de Mesa'),
        ('Bloques', 'Bloques'),
        ('Vehículos', 'Vehículos'),
        ('Outdoor', 'Outdoor'),
        ('Electronicos', 'Electronicos'),
        ('Educativo', 'Educativo'),
        ('Muñecas', 'Muñecas'),
        ('Otro', 'Otro')
    ]
    category = SelectField('Categoría', choices=CATEGORIES, validators=[DataRequired()])
    stock = IntegerField('Cantidad en Stock', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Imagen del Juguete', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '¡Solo imágenes!')])
    submit = SubmitField('Guardar Juguete')

class AddUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    # Definir opciones de centros
    CENTERS = [
        ('Aloha Central', 'Aloha Central'),
        ('Sucursal Norte', 'Sucursal Norte'),
        ('Sucursal Sur', 'Sucursal Sur'),
        ('Sucursal Este', 'Sucursal Este'),
        ('Sucursal Oeste', 'Sucursal Oeste')
    ]
    center = SelectField('Centro/Sucursal', choices=CENTERS, validators=[DataRequired()])
    is_admin = BooleanField('¿Es Administrador?', default=False)
    is_active = BooleanField('¿Está Activo?', default=True)
    submit = SubmitField('Agregar Usuario')

class EditUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email(), Length(max=120)])
    new_password = PasswordField('Nueva Contraseña (dejar en blanco para no cambiar)', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmar Nueva Contraseña', validators=[EqualTo('new_password', message='Las nuevas contraseñas deben coincidir.')])
    center = SelectField('Centro/Sucursal', choices=AddUserForm.CENTERS, validators=[DataRequired()])
    is_admin = BooleanField('¿Es Administrador?')
    is_active = BooleanField('¿Está Activo?')
    submit = SubmitField('Guardar Cambios')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    # Custom validation for password confirmation only if new_password is provided
    def validate_confirm_new_password(self, field):
        if self.new_password.data and not field.data:
            raise ValidationError('Por favor, confirma la nueva contraseña.')
        if self.new_password.data and field.data != self.new_password.data:
            # This is already handled by EqualTo, but an explicit check can be clearer or allow custom messages
            pass # EqualTo validator handles this
