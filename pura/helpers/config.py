from os import getenv
mail_config = {
    'imap': {
        'server': getenv('IMAP_SERVER'),
        'port': getenv('IMAP_PORT')
    },
    'smtp': {
        'server': getenv('SMTP_SERVER'),
        'port': getenv('SMTP_PORT')
    },
    'auth': {
        'user': getenv('MAIL_USER'),
        'pass': getenv('MAIL_PASS')
    },
    'default_mailbox': getenv('DEFAULT_MAILBOX', 'inbox')
}
