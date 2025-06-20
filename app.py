from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
from datetime import datetime, timedelta
from functools import wraps
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from flask_talisman import Talisman
from flask import jsonify
import uuid
import base64
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Пользователи с паролями и ролями
users = {
    "admin": {"password": "password", "role": "admin"},
    "omsu_user": {"password": "omsu_pass", "role": "omsu"},
    "oigv_user": {"password": "oigv_pass", "role": "oigv"},
    "governor_user": {"password": "governor_pass", "role": "governor"},
}

NONCE = base64.b64encode(os.urandom(16)).decode('utf-8')

Talisman(
    app,
    content_security_policy={
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "https://cdn.jsdelivr.net",   # CDN для FullCalendar и Bootstrap
            "'unsafe-eval'",              # Требуется для FullCalendar
            "'unsafe-inline'"             # Временно разрешаем inline-скрипты
        ],
        'style-src': [
            "'self'",
            "https://cdn.jsdelivr.net",
            "'unsafe-inline'"             # Разрешаем инлайновые стили (временно)
        ],
        'img-src': [
            "'self'",
            "data:",
            "https://cdn.jsdelivr.net"
        ],
        'font-src': [
            "'self'",
            "https://cdn.jsdelivr.net"
        ]
    },
    force_https=False  # Только для локальной разработки
)
# Глобальное хранилище уведомлений
notifications = []
def get_risk_color(criticality):
    colors = {
        "Зеленый": "#28a745",
        "Желтый": "#ffc107",
        "Красный": "#dc3545",
        "Черный": "#000000"
    }
    return colors.get(criticality, "#6c757d")

@app.context_processor
def utility_functions():
    def get_risk_color(criticality):
        colors = {
            "Зеленый": "#28a745",
            "Желтый": "#ffc107",
            "Красный": "#dc3545",
            "Черный": "#000000"
        }
        return colors.get(criticality, "#6c757d")

    def get_status_color(status):
        colors = {
            "Новый": "#0d6efd",
            "Взято в работу": "#20c997",
            "Отработан": "#198754"
        }
        return colors.get(status, "#6c757d")

    return dict(get_risk_color=get_risk_color, get_status_color=get_status_color)





# Декоратор проверки ролей
def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                flash("Для доступа к этой странице необходимо войти.", "danger")
                return redirect(url_for('login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash("У вас нет прав для доступа к этой странице.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Вспомогательные данные
categories = ["Дороги", "ЖКХ", "Благоустройство", "Здравоохранение", "Транспорт", "Экология"]
municipalities = ["Вологда", "Череповец", "Вологодский округ"]
criticality_levels = ["Зеленый", "Желтый", "Красный", "Черный"]
statuses = ["Новый", "Взято в работу", "Отработан"]

# Тестовые риски
risks = [
    {
        "id": str(uuid.uuid4()),  # Уникальный идентификатор
        "title": f"Тестовый риск {i + 1}",
        "source": f"Источник {i % 3 + 1}",
        "date_added": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d %H:%M"),
        "deadline_value": 24,
        "deadline_unit": "hours",
        "is_repeating": False,
        "description": f"Описание тестового риска {i + 1}",
        "justification": f"Обоснование тестового риска {i + 1}",
        "category": categories[i % len(categories)],
        "omsu": municipalities[i % len(municipalities)],
        "oigv": "ОИГВ Пример",
        "deputy": "Заместитель Пример",
        "municipality": municipalities[i % len(municipalities)],
        "criticality": criticality_levels[i % len(criticality_levels)],
        "status": statuses[i % len(statuses)],
        "closed_at": None,
        "comments": [],  # Инициализация списка комментариев
        "attachments": []  # Инициализация списка вложений
    }
    for i in range(500)
]


def get_archived_risks_from_db():
    return [risk for risk in risks if risk['status'] == 'Отработан']


@app.route('/')
@roles_required('admin', 'omsu', 'oigv', 'governor')
def index():
    sort_by = request.args.get('sort_by', 'date_added')
    filter_status = request.args.get('filter_status', '')
    filter_criticality = request.args.get('filter_criticality', '')
    filter_municipality = request.args.get('filter_municipality', '')

    filtered = risks[:]

    if filter_status:
        filtered = [r for r in filtered if r['status'] == filter_status]
    if filter_criticality:
        filtered = [r for r in filtered if r['criticality'] == filter_criticality]
    if filter_municipality:
        filtered = [r for r in filtered if r['municipality'] == filter_municipality]

    try:
        reverse = request.args.get('reverse', 'false').lower() == 'true'
        # Дефолтная сортировка по дате добавления, от старых к новым
        if sort_by == 'date_added' or sort_by not in risks[0]:
            filtered.sort(key=lambda x: x['date_added'], reverse=False)
        else:
            filtered.sort(key=lambda x: x.get(sort_by, ''), reverse=reverse)
    except KeyError:
        pass

    return render_template(
        'index.html',
        risks=filtered,
        statuses=statuses,
        criticality_levels=criticality_levels,
        municipalities=municipalities
    )

@app.route('/upload_attachment/<int:index>', methods=['POST'])
@roles_required('admin', 'omsu', 'oigv', 'governor')
def upload_attachment(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    file = request.files.get('attachment')
    if file and file.filename:
        filename = f"{index}_{file.filename}"
        file.save(os.path.join('static', 'uploads', filename))
        risks[index]['attachments'].append({
            'filename': filename,
            'url': f"/static/uploads/{filename}"
        })
        flash("Файл успешно загружен", "success")
    return redirect(url_for('risk_detail', index=index))


@app.route('/add_comment/<int:index>', methods=['POST'])
@roles_required('admin', 'omsu', 'oigv', 'governor')
def add_comment(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    comment_text = request.form.get('comment_text', '').strip()
    if comment_text:
        risks[index]['comments'].append({
            'author': session['username'],
            'text': comment_text,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        flash("Комментарий добавлен", "success")
    return redirect(url_for('risk_detail', index=index))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = users.get(username)
        if user and user['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user['role']
            flash(f"Вы успешно вошли как {user['role']}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Неверные учетные данные.", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Вы успешно вышли.", "info")
    return redirect(url_for('login'))


@app.route('/risk/<int:index>')
@roles_required('admin', 'omsu', 'oigv', 'governor')
def risk_detail(index):
    if index < 0 or index >= len(risks):
        abort(404)
    risk = risks[index].copy()
    try:
        created_at = datetime.strptime(risk['date_added'], "%Y-%m-%d %H:%M")
        risk['created_at_str'] = created_at.strftime('%d.%m.%Y %H:%M')
    except Exception:
        risk['created_at_str'] = 'Нет даты'
    return render_template(
        'risk_detail.html',
        risk=risk,
        get_risk_color=get_risk_color,
        index=index,
        from_page='calendar'  # ← Добавляем источник страницы
    )


@app.route('/add_risk', methods=['GET', 'POST'])
@roles_required('admin', 'omsu')
def add_risk():
    if request.method == 'POST':
        try:
            deadline_value = int(request.form.get('deadline_value', 1))
            deadline_unit = request.form.get('deadline_unit', 'hours')
        except ValueError:
            flash("Неверное значение срока.", "danger")
            return redirect(url_for('add_risk'))

        now = datetime.now()
        deadline = now + (
            timedelta(hours=deadline_value) if deadline_unit == 'hours' else timedelta(days=deadline_value)
        )

        risk = {
            "title": request.form.get('title', ''),
            "source": request.form.get('source', ''),
            "date_added": now.strftime("%Y-%m-%d %H:%M"),
            "deadline_value": deadline_value,
            "deadline_unit": deadline_unit,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "is_repeating": 'is_repeating' in request.form,
            "description": request.form.get('description', ''),
            "justification": request.form.get('justification', ''),
            "category": request.form.get('category', ''),
            "omsu": request.form.get('omsu', ''),
            "oigv": request.form.get('oigv', ''),
            "deputy": request.form.get('deputy', ''),
            "municipality": request.form.get('municipality', ''),
            "criticality": request.form.get('criticality', ''),
            "status": "Новый",
            "closed_at": None,
            "comments": [],
            "attachments": []
        }
        risks.append(risk)
        flash("Риск успешно добавлен!", "success")
        return redirect(url_for('index'))

    return render_template(
        'risk_form.html',
        risk=None,
        categories=categories,
        municipalities=municipalities,
        criticality_levels=criticality_levels
    )


@app.route('/edit_risk/<int:index>', methods=['GET', 'POST'])
@roles_required('admin', 'omsu')
def edit_risk(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    risk = risks[index]
    if request.method == 'POST':
        try:
            deadline_value = int(request.form.get('deadline_value', 1))
            deadline_unit = request.form.get('deadline_unit', 'hours')
        except ValueError:
            flash("Неверное значение срока.", "danger")
            return redirect(url_for('edit_risk', index=index))

        now = datetime.now()
        deadline = now + (
            timedelta(hours=deadline_value) if deadline_unit == 'hours' else timedelta(days=deadline_value)
        )

        risk.update({
            "title": request.form.get('title', ''),
            "source": request.form.get('source', ''),
            "deadline_value": deadline_value,
            "deadline_unit": deadline_unit,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "is_repeating": 'is_repeating' in request.form,
            "description": request.form.get('description', ''),
            "justification": request.form.get('justification', ''),
            "category": request.form.get('category', ''),
            "omsu": request.form.get('omsu', ''),
            "oigv": request.form.get('oigv', ''),
            "deputy": request.form.get('deputy', ''),
            "municipality": request.form.get('municipality', ''),
            "criticality": request.form.get('criticality', '')
        })
        flash("Риск успешно обновлен!", "success")
        return redirect(url_for('index'))

    return render_template(
        'risk_form.html',
        risk=risk,
        categories=categories,
        municipalities=municipalities,
        criticality_levels=criticality_levels
    )


@app.route('/close_risk/<int:index>')
@roles_required('admin')
def close_risk(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    risks[index]['status'] = "Отработан"
    risks[index]['closed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    flash("Риск закрыт и отправлен в архив.", "success")
    return redirect(url_for('archive'))


@app.route('/take_risk/<int:index>')
@roles_required('admin','omsu', 'oigv', 'governor')
def take_risk(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    risk = risks[index]
    risk['status'] = "Взято в работу"
    flash("Статус изменён: Взято в работу", "success")
    return redirect(url_for('index'))


@app.route('/complete_risk/<int:index>')
@roles_required('omsu', 'oigv', 'governor')
def complete_risk(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    risk = risks[index]
    risk['status'] = "Отработан"
    risk['closed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    flash("Статус изменён: Отработан", "success")
    return redirect(url_for('index'))


@app.route('/archive')
@roles_required('admin', 'governor')
def archive():
    archived = get_archived_risks_from_db()
    return render_template('archive.html', archived=archived)


@app.route('/notifications')
@roles_required('omsu', 'oigv', 'governor')
def view_notifications():
    user_role = session.get('role')
    user_notifications = [n for n in notifications if n['role'] == user_role]
    return render_template('notifications.html', notifications=user_notifications)


@app.route('/calendar')
@roles_required('admin', 'governor', 'omsu', 'oigv')
def calendar():
    return render_template('calendar.html', risks=risks)


@app.route('/calendar_events')
@roles_required('admin', 'governor', 'omsu', 'oigv')
def calendar_events():
    """Возвращает события для FullCalendar"""
    events = []
    for i, risk in enumerate(risks):
        # Основное событие — дата добавления
        events.append({
            'title': 'Риск',
            'start': risk['date_added'],
            'color': get_risk_color(risk['criticality']),
            'url': url_for('risk_detail', index=i)
        })
        # Дополнительное событие — дедлайн, если есть
        if 'deadline' in risk and risk['deadline']:
            events.append({
                'title': 'Риск (дедлайн)',
                'start': risk['deadline'],
                'color': '#ff0000',
                'url': url_for('risk_detail', index=i)
            })
    return jsonify(events)


@app.route('/report', methods=['GET', 'POST'])
@roles_required('admin', 'governor', 'omsu', 'oigv')
def report():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    period = request.form.get('period')
    now = datetime.now()

    if period == 'day':
        start_date = now.strftime("%Y-%m-%d 00:00")
        end_date = now.strftime("%Y-%m-%d 23:59")
    elif period == 'week':
        start_of_week = now - timedelta(days=now.weekday())
        start_date = start_of_week.strftime("%Y-%m-%d 00:00")
        end_date = (start_of_week + timedelta(days=6)).strftime("%Y-%m-%d 23:59")
    elif period == 'month':
        first_day = now.replace(day=1)
        next_month = first_day.replace(month=first_day.month % 12 + 1,
                                       day=1) if first_day.month < 12 else first_day.replace(year=first_day.year + 1,
                                                                                             month=1, day=1)
        last_day = next_month - timedelta(days=1)
        start_date = first_day.strftime("%Y-%m-%d 00:00")
        end_date = last_day.strftime("%Y-%m-%d 23:59")
    elif period == 'quarter':
        quarter = (now.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start_date = datetime(now.year, start_month, 1).strftime("%Y-%m-%d 00:00")
        end_month = start_month + 2
        end_date = datetime(now.year, end_month, 1).replace(day=1, month=end_month) + timedelta(days=32)
        end_date = end_date.replace(day=1) - timedelta(days=1)
        end_date = end_date.strftime("%Y-%m-%d 23:59")
    elif period == 'year':
        start_date = datetime(now.year, 1, 1).strftime("%Y-%m-%d 00:00")
        end_date = datetime(now.year, 12, 31).strftime("%Y-%m-%d 23:59")
    elif period == 'all':
        start_date = "1900-01-01 00:00"
        end_date = "2100-12-31 23:59"

    filtered_risks = []
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        end = datetime.strptime(end_date, "%Y-%m-%d %H:%M")
        for risk in risks:
            added = datetime.strptime(risk['date_added'], "%Y-%m-%d %H:%M")
            closed = risk.get('closed_at')
            closed_time = datetime.strptime(closed, "%Y-%m-%d %H:%M") if closed else None
            if start <= added <= end or (closed_time and start <= closed_time <= end):
                filtered_risks.append(risk)
    except Exception:
        filtered_risks = []

    return render_template('report_form.html', risks=filtered_risks, start_date=start_date, end_date=end_date)


@app.route('/export_report/<format>')
def export_report(format):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    filtered_risks = []

    if not start_date or not end_date:
        return "Дата не указана", 400

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        end = datetime.strptime(end_date, "%Y-%m-%d %H:%M")

        for risk in risks:
            added = datetime.strptime(risk['date_added'], "%Y-%m-%d %H:%M")
            if start <= added <= end:
                filtered_risks.append(risk)
    except Exception as e:
        print(f"Ошибка при фильтрации рисков: {e}")
        return "Ошибка формата даты", 400

    if format == 'excel':
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append([
            "Название", "Дата добавления", "Дата отработки", "ОМСУ", "ОИГВ", "Заместитель", "Муниципалитет"
        ])
        for r in filtered_risks:
            ws.append([
                r.get('title', ''),
                r.get('date_added', ''),
                r.get('closed_at', ''),
                r.get('omsu', ''),
                r.get('oigv', ''),
                r.get('deputy', ''),
                r.get('municipality', '')
            ])
        report_filename = "report.xlsx"
        wb.save(report_filename)
        return send_file(report_filename, as_attachment=True)
    elif format == 'pdf':
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
            use_custom_font = True
        except Exception:
            use_custom_font = False

        pdf_path = "report.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        style = styles["Normal"]
        data = [["Название", "Дата добавления", "Дата отработки", "Исполнители", "Муниципалитет"]]

        for r in filtered_risks:
            data.append([
                r.get('title', ''),
                r.get('date_added', ''),
                r.get('closed_at', '—'),
                f"ОМСУ: {r.get('omsu', '')}\nОИГВ: {r.get('oigv', '')}\nЗаместитель: {r.get('deputy', '')}",
                r.get('municipality', '')
            ])

        table = Table(data, colWidths=[100, 100, 100, 170, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#cccccc'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f2f2f2'),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu') if use_custom_font else ('FONTNAME', (0, 0), (-1, -1), 'Helvetica')
        ]))
        doc.build([table])
        return send_file(pdf_path, as_attachment=True)
    else:
        return "Unsupported format", 400


@app.route('/update_status/<int:index>', methods=['POST'])
def update_status(index):
    if index < 0 or index >= len(risks):
        flash("Риск не найден", "danger")
        return redirect(url_for('index'))

    new_status = request.form['status']
    risks[index]['status'] = new_status
    flash(f"Статус изменён: {new_status}", "info")
    return redirect(url_for('calendar'))


if __name__ == '__main__':
    import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
