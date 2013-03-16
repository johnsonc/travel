from jargon.apps.mailer import send_mail

#-------------------------------------------------------------------------------
def send_message(user, title, message):
    send_mail(title, 'From %s: (%s)\n\n%s' % (
        user.get_full_name, 
        user.email,
        form.cleaned_data['message']
    ))
