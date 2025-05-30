from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from models import Risk, ChatMessage, Notification, db
from forms import RiskForm, ChatMessageForm
from datetime import datetime
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def create_risk_notification(risk, message_text):
    recipients = []

    if risk.omsu:
        omsu_user = User.query.filter_by(username=risk.omsu).first()
        if omsu_user:
            recipients.append(omsu_user)

    if risk.oigv:
        oigv_user = User.query.filter_by(username=risk.oigv).first()
        if oigv_user:
            recipients.append(oigv_user)

    if risk.governor:
        governor_user = User.query.filter_by(username=risk.governor).first()
        if governor_user:
            recipients.append(governor_user)

    for user in recipients:
        notification = Notification(
            user_id=user.id,
            risk_id=risk.id,
            message=message_text
        )
        db.session.add(notification)
    db.session.commit()


@main_bp.route('/')
@login_required
def index():
    risks = Risk.query.all()
    return render_template('index.html', risks=risks)


@main_bp.route('/risk/new', methods=['GET', 'POST'])
@login_required
def new_risk():
    form = RiskForm()
    if form.validate_on_submit():
        risk = Risk(
            title=form.title.data,
            source_link=form.source_link.data,
            date_added=form.date_added.data,
            time_to_resolve_hours=form.time_to_resolve_hours.data,
            is_repeating=form.is_repeating.data,
            description=form.description.data,
            justification=form.justification.data,
            category=form.category.data,
            omsu=form.omsu.data,
            oigv=form.oigv.data,
            governor=form.governor.data,
            municipality=form.municipality.data,
            severity=form.severity.data
        )
        db.session.add(risk)
        db.session.commit()

        create_risk_notification(risk, f"Новый риск: {risk.title}")

        flash('Риск успешно добавлен!')
        return redirect(url_for('main.index'))
    return render_template('risk.form.html', form=form)


@main_bp.route('/risk/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_risk(id):
    risk = Risk.query.get_or_404(id)
    form = RiskForm(obj=risk)
    if form.validate_on_submit():
        form.populate_obj(risk)
        db.session.commit()

        create_risk_notification(risk, f"Риск обновлён: {risk.title}")

        flash('Риск успешно обновлён.')
        return redirect(url_for('main.index'))
    return render_template('risk.form.html', form=form, risk=risk)


@main_bp.route('/risk/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_risk(id):
    risk = Risk.query.get_or_404(id)
    risk.is_resolved = True
    risk.date_resolved = datetime.utcnow()
    db.session.commit()
    flash('Риск закрыт.')
    return redirect(url_for('main.index'))


@main_bp.route('/calendar')
@login_required
def calendar():
    risks = Risk.query.all()
    return render_template('calendar.html', risks=risks)


@main_bp.route('/risk/<int:id>/detail', methods=['GET', 'POST'])
@login_required
def risk_detail(id):
    risk = Risk.query.get_or_404(id)
    form = ChatMessageForm()

    if form.validate_on_submit():
        message = ChatMessage(
            text=form.text.data,
            risk_id=risk.id,
            user_id=current_user.id
        )

        if form.attachment.data:
            file = form.attachment.data
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            message.file_path = filepath

        db.session.add(message)
        db.session.commit()
        flash('Сообщение отправлено!')

        return redirect(url_for('main.risk_detail', id=id))

    messages = ChatMessage.query.filter_by(risk_id=risk.id).order_by(ChatMessage.timestamp.asc()).all()
    return render_template('risk.detail.html', risk=risk, form=form, messages=messages)


@main_bp.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifs)