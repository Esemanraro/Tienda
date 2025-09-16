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
        ('Sensorial', 'Sensorial'),
        ('Juego', 'Juego'),
        ('Accesorio', 'Accesorio'),
        ('Bloques', 'Bloques'),
        ('Vehículos', 'Vehículos'),
        ('Outdoor', 'Outdoor'),
        ('Electrónicos', 'Electrónicos'),
        ('Educativo', 'Educativo'),
        ('Muñecas', 'Muñecas'),
        ('Otro', 'Otro'),
        ('0-3', '0-3 años'),
        ('4-6', '4-6 años'),
        ('7-9', '7-9 años'),
        ('10+', '10+ años')
    ]
    # Allow categories not present in the predefined list and make optional for edits
    category = SelectField(
        'Categoría',
        choices=CATEGORIES,
        validators=[Optional()],
        validate_choice=False
    )
    # Campos separados para categorias
    TOY_TYPE_CHOICES = [
        ('Figuras', 'Figuras'),
        ('Peluches', 'Peluches'),
        ('Juegos de Mesa', 'Juegos de Mesa'),
        ('Sensorial', 'Sensorial'),
        ('Juego', 'Juego'),
        ('Accesorio', 'Accesorio'),
        ('Bloques', 'Bloques'),
        ('Vehículos', 'Vehículos'),
        ('Outdoor', 'Outdoor'),
        ('Electrónicos', 'Electrónicos'),
        ('Educativo', 'Educativo'),
        ('Muñecas', 'Muñecas'),
        ('Otro', 'Otro'),
    ]
    GENDER_CHOICES = [
        ('Niña', 'Niña'),
        ('Niño', 'Niño'),
        ('Mixto', 'Mixto'),
    ]
    AGE_CHOICES = [
        ('0-3', '0-3 años'),
        ('4-6', '4-6 años'),
        ('7-9', '7-9 años'),
        ('10+', '10+ años'),
    ]
    # Make category fields optional during edit operations
    toy_type = SelectField(
        'Categoria de Juguete',
        choices=TOY_TYPE_CHOICES,
        validators=[Optional()],
        validate_choice=False
    )
    gender = SelectField(
        'Categoria de Genero',
        choices=GENDER_CHOICES,
        validators=[Optional()],
        validate_choice=False
    )
    age_range = SelectField(
        'Categoria de Edad',
        choices=AGE_CHOICES,
        validators=[Optional()],
        validate_choice=False
    )
    stock = IntegerField('Cantidad en Stock', validators=[Optional(), NumberRange(min=0)])
    image = FileField('Imagen del Juguete', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '¡Solo imágenes!')])
    submit = SubmitField('Guardar Juguete')

class AddUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(
        'Correo Electrónico',
        validators=[Optional(), Email(), Length(max=120)],
        filters=[lambda value: value.strip() if value else None]
    )
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
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
        ('escuela bet yacoov', 'Escuela Bet Yacoov'),
        ('escuela de la salle', 'Escuela De La Salle'),
    ]
    center = SelectField('Centro/Sucursal', choices=CENTERS, validators=[DataRequired()])
    balance = FloatField('Saldo Inicial (A$)', validators=[Optional(), NumberRange(min=0)])
    require_password_change = BooleanField('Requerir cambio de contraseA�a al primer ingreso', default=True)
    is_admin = BooleanField('¿Es Administrador?', default=False)
    is_active = BooleanField('¿Está Activo?', default=True)
    submit = SubmitField('Agregar Usuario')

class EditUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(
        'Correo Electrónico',
        validators=[Optional(), Email(), Length(max=120)],
        filters=[lambda value: value.strip() if value else None]
    )
    new_password = PasswordField('Nueva Contraseña (dejar en blanco para no cambiar)', validators=[Optional(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmar Nueva Contraseña', validators=[EqualTo('new_password', message='Las nuevas contraseñas deben coincidir.')])
    center = SelectField('Centro/Sucursal', choices=AddUserForm.CENTERS, validators=[DataRequired()])
    balance = FloatField('Saldo (A$)', validators=[Optional(), NumberRange(min=0)])
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


