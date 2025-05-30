from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, BooleanField, IntegerField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed

# === Форма логина ===
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


# === Форма риска ===
SEVERITY_CHOICES = [
    ('green', 'Зеленый'),
    ('yellow', 'Желтый'),
    ('red', 'Красный'),
    ('black', 'Черный')
]

CATEGORY_CHOICES = [
    ('roads', 'Дороги'),
    ('housing', 'ЖКХ'),
    ('improvement', 'Благоустройство'),
    ('healthcare', 'Здравоохранение'),
    ('transport', 'Транспорт'),
    ('ecology', 'Экология')
]

MUNICIPALITY_CHOICES = [
    ('vologda', 'Вологда'),
    ('cherepovets', 'Череповец'),
    ('vologodskiy_okrug', 'Вологодский округ')
]

OMSU_CHOICES = [('omsu_1', 'ОМСУ 1'), ('omsu_2', 'ОМСУ 2')]
OIGV_CHOICES = [('oigv_1', 'ОИГВ 1'), ('oigv_2', 'ОИГВ 2')]
GOVERNOR_CHOICES = [('gov_1', 'Губернатор 1'), ('gov_2', 'Губернатор 2')]


class RiskForm(FlaskForm):
    title = StringField('Название риска', validators=[DataRequired()])
    source_link = StringField('Ссылка на источник')
    date_added = DateTimeField('Дата и время добавления', format='%Y-%m-%d %H:%M')
    time_to_resolve_hours = IntegerField('Срок отработки (в часах)')
    is_repeating = BooleanField('Повторяющийся риск')
    description = TextAreaField('Описание')
    justification = TextAreaField('Обоснование')

    category = SelectField('Категория', choices=CATEGORY_CHOICES)
    omsu = SelectField('ОМСУ', choices=OMSU_CHOICES)
    oigv = SelectField('ОИГВ', choices=OIGV_CHOICES)
    governor = SelectField('Куратор от губернатора', choices=GOVERNOR_CHOICES)

    municipality = SelectField('Муниципалитет', choices=MUNICIPALITY_CHOICES)
    severity = SelectField('Критичность', choices=SEVERITY_CHOICES)

    submit = SubmitField('Сохранить риск')


# === Форма чата ===
class ChatMessageForm(FlaskForm):
    text = TextAreaField('Сообщение')
    attachment = FileField('Прикрепить файл', validators=[
        FileAllowed(['jpg', 'png', 'pdf', 'docx', 'xlsx'], 'Только изображения и документы!')
    ])
    submit = SubmitField('Отправить')