from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Length, Email, EqualTo, Optional, ValidationError # Added Email, EqualTo, Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed

class ToyForm(FlaskForm):
    name = StringField('Nombre del Juguete', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('DescripciÃ³n')
    price = FloatField('Precio (A$)', validators=[DataRequired(), NumberRange(min=0.01)])
    # CategorÃ­as pregrabadas (incluye las categorÃ­as existentes en la base de datos)
    CATEGORIES = [
        ('NiÃ±a', 'NiÃ±a'),
        ('NiÃ±o', 'NiÃ±o'),
        ('Mixto', 'Mixto'),
        ('Figuras', 'Figuras'),
        ('Peluches', 'Peluches'),
        ('Juegos de Mesa', 'Juegos de Mesa'),
        ('Bloques', 'Bloques'),
        ('VehÃ­culos', 'VehÃ­culos'),
        ('Outdoor', 'Outdoor'),
        ('Electronicos', 'Electronicos'),
        ('Educativo', 'Educativo'),
        ('MuÃ±ecas', 'MuÃ±ecas'),
        ('Otro', 'Otro'),
        ('0-3', '0-3 aÃ±os'),
        ('4-6', '4-6 aÃ±os'),
        ('7-9', '7-9 aÃ±os'),
        ('10+', '10+ aÃ±os')
    ]
    category = SelectField('CategorÃ­a', choices=CATEGORIES, validators=[Optional()])
    # Campos separados para categorias
    TOY_TYPE_CHOICES = [
        ('Figuras', 'Figuras'),
        ('Peluches', 'Peluches'),
        ('Juegos de Mesa', 'Juegos de Mesa'),
        ('Bloques', 'Bloques'),
        ('Vehiculos', 'Vehiculos'),
        ('Outdoor', 'Outdoor'),
        ('Electronicos', 'Electronicos'),
        ('Educativo', 'Educativo'),
        ('Munecas', 'Munecas'),
        ('Otro', 'Otro'),
    ]
    GENDER_CHOICES = [
        ('Nina', 'Nina'),
        ('Nino', 'Nino'),
        ('Mixto', 'Mixto'),
    ]
    AGE_CHOICES = [
        ('0-3', '0-3 anos'),
        ('4-6', '4-6 anos'),
        ('7-9', '7-9 anos'),
        ('10+', '10+ anos'),
    ]
    toy_type = SelectField('Categoria de Juguete', choices=TOY_TYPE_CHOICES, validators=[DataRequired()])
    gender = SelectField('Categoria de Genero', choices=GENDER_CHOICES, validators=[DataRequired()])
    age_range = SelectField('Categoria de Edad', choices=AGE_CHOICES, validators=[DataRequired()])
    stock = IntegerField('Cantidad en Stock', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Imagen del Juguete', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Â¡Solo imÃ¡genes!')])
    submit = SubmitField('Guardar Juguete')

class AddUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Correo ElectrÃ³nico', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('ContraseÃ±a', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar ContraseÃ±a', validators=[DataRequired(), EqualTo('password', message='Las contraseÃ±as deben coincidir.')])
    # Definir opciones de centros (ALOHA locations)
    CENTERS = [
        ('aguadulce', 'Aguadulce'),
        ('anclas mall', 'Anclas Mall'),
        ('brisas del golf', 'Brisas del Golf'),
        ('calle 50', 'Calle 50'),
        ('costa del este', 'Costa del Este'),
        ('david', 'David'),
        ('chitre', 'Chitre'),
        ('santiago', 'Santiago'),
        ('condado del rey', 'Condado Del Rey'),
        ('centro autorizado arraijan', 'Centro Autorizado Arraijan'),
    ]
    center = SelectField('Centro/Sucursal', choices=CENTERS, validators=[DataRequired()])
    is_admin = BooleanField('Â¿Es Administrador?', default=False)
    is_active = BooleanField('Â¿EstÃ¡ Activo?', default=True)
    submit = SubmitField('Agregar Usuario')

class EditUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Correo ElectrÃ³nico', validators=[DataRequired(), Email(), Length(max=120)])
    new_password = PasswordField('Nueva ContraseÃ±a (dejar en blanco para no cambiar)', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmar Nueva ContraseÃ±a', validators=[EqualTo('new_password', message='Las nuevas contraseÃ±as deben coincidir.')])
    center = SelectField('Centro/Sucursal', choices=AddUserForm.CENTERS, validators=[DataRequired()])
    is_admin = BooleanField('Â¿Es Administrador?')
    is_active = BooleanField('Â¿EstÃ¡ Activo?')
    submit = SubmitField('Guardar Cambios')

    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    # Custom validation for password confirmation only if new_password is provided
    def validate_confirm_new_password(self, field):
        if self.new_password.data and not field.data:
            raise ValidationError('Por favor, confirma la nueva contraseÃ±a.')
        if self.new_password.data and field.data != self.new_password.data:
            # This is already handled by EqualTo, but an explicit check can be clearer or allow custom messages
            pass # EqualTo validator handles this

