"""Async worker for rating comment notifications."""

import logging

import ckan.model as model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


def send_rating_comment_notifications(package_id: str, rating_id: str) -> None:
    """Resolve recipients and send comment notification emails."""
    from ckan.lib import mailer

    from ckanext.artesp_theme.model import DatasetRating

    rating = model.Session.query(DatasetRating).get(rating_id)
    if not rating or not rating.comment:
        return

    pkg_dict = tk.get_action("package_show")(
        {"ignore_auth": True}, {"id": package_id}
    )

    author = model.User.get(rating.user_id)
    author_name = (
        (author.fullname or author.name) if author else tk._("Usuário desconhecido")
    )

    recipients = _resolve_recipients(pkg_dict, rating.user_id)
    if not recipients:
        log.info("rating_notifications job rating=%s recipients=0", rating_id)
        return

    dataset_title = pkg_dict.get("title") or pkg_dict.get("name")
    subject = tk._(
        "Novo comentário de avaliação no conjunto de dados: {title}"
    ).format(title=dataset_title)
    body = tk._(
        "O usuário {author} enviou um comentário de avaliação no conjunto de dados '{title}':\n\n{comment}"
    ).format(
        author=author_name,
        title=dataset_title,
        comment=rating.comment,
    )

    sent = 0
    for user in recipients:
        try:
            mailer.mail_user(user, subject, body)
            sent += 1
        except mailer.MailerException as exc:
            log.warning(
                "rating_notifications recipient_failed user=%s error=%s", user.id, exc
            )

    log.info("rating_notifications job=%s recipients=%d sent=%d", rating_id, len(recipients), sent)


def _resolve_recipients(pkg_dict: dict, author_user_id: str) -> list:
    """Return deduplicated list of User objects to notify."""
    seen_ids: set = set()
    seen_emails: set = set()
    recipients: list = []

    def _is_active(user) -> bool:
        active = getattr(user, "is_active", False)
        return active() if callable(active) else bool(active)

    def _add(user):
        if not user or not _is_active(user):
            return
        if user.id in seen_ids:
            return
        email = (user.email or "").strip().lower()
        if not email or email in seen_emails:
            return
        if user.id == author_user_id:
            return
        seen_ids.add(user.id)
        seen_emails.add(email)
        recipients.append(user)

    for sysadmin in model.Session.query(model.User).filter_by(sysadmin=True, state="active").all():
        _add(sysadmin)

    if pkg_dict.get("creator_user_id"):
        _add(model.User.get(pkg_dict["creator_user_id"]))

    try:
        collaborators = tk.get_action("package_collaborator_list")(
            {"ignore_auth": True}, {"id": pkg_dict["id"]}
        )
        for collab in collaborators:
            _add(model.User.get(collab.get("user_id") or collab.get("id")))
    except tk.ValidationError:
        pass

    return recipients
