from flask_wtf.file import FileRequired
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm as Form


class LoginForm(Form):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit_login = SubmitField("Iniciar sesion")


class UploadFileForm(Form):
    file = FileField("Archivo", validators=[FileRequired()])
    validate = SubmitField("Validar")
    submit = SubmitField("Subir")


