send_from = 'margolisys@gmail.com'
send_to = 'office@margolisys.com'
app_pass = 'jhjmttwbgosodkcf'


def send2():
    import smtplib
    import ssl

    port = 587  # For starttls
    smtp_server = "smtp.gmail.com"
    sender_email = send_from
    receiver_email = send_to
    password = app_pass
    message = """\
    "From: margolisys@gmail.com",
    "To: office@margolisys.com",
    Subject: Hi there

    This message is sent from Python."""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


if __name__ == '__manin__':
    send2()
