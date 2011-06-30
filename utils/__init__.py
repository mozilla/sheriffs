def get_user_name(user):
    if user.first_name:
        return (u'%s %s (%s)' %
                 (user.first_name,
                  user.last_name,
                  user.username))
    return user.username
