import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

log = logging.getLogger(__name__)

@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    if 'X-Forwarded-For' in request.META:
        ip = request.META.get('X-Forwarded-For')
    log.warning('Login SUCCESS: [{ip}] User: {user}'.format(
        ip=ip,
        user=user.username,
    ))


@receiver(user_login_failed)
def user_login_failed_callback(sender, credentials, request, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    if 'X-Forwarded-For' in request.META:
        ip = request.META.get('X-Forwarded-For')
    log.warning('Login FAILED: [{ip}] User: {username}'.format(
        username=credentials['username'],
        ip=ip
    ))
