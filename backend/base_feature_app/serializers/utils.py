from base_feature_app.utils.shelter_access import (
    is_web_manager_or_admin,
    shelters_managed_by_user,
)


def can_view_shelter_owner_email(serializer, shelter):
    """Keep account e-mails private, sharing one permission query across rows."""
    context = serializer.context
    request = context.get('request')
    if request is None or not request.user.is_authenticated:
        return False
    if is_web_manager_or_admin(request.user):
        return True

    # A ListSerializer and its child share the root context. Cache IDs there,
    # never on the user or globally, so authorization costs one query per request.
    scope_key = '_owner_email_managed_shelter_ids'
    if scope_key not in context:
        context[scope_key] = frozenset(
            shelters_managed_by_user(request.user).values_list('pk', flat=True)
        )
    return shelter.pk in context[scope_key]


def get_lang(serializer):
    """Return 'es' or 'en' from serializer context (default 'es')."""
    request = serializer.context.get('request')
    if request:
        lang = request.query_params.get('lang', 'es')
        return lang if lang in ('es', 'en') else 'es'
    return serializer.context.get('lang', 'es')


def library_primary_url(library, default=''):
    """Return the URL of a Library's primary attachment, or `default` if missing."""
    if library and library.primary_attachment:
        return library.primary_attachment.file.url
    return default
