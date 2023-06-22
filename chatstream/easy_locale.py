import locale


class EasyLocale:
    """
    A helper class to handle localization. It supports English and Japanese languages, and falls back to English
    by default if the requested locale is not supported.
    """

    def __init__(self, opts=None):
        """
        Initialize an EasyLocale object.

        :param opts: A dictionary of options for initialization. It can contain keys 'fallback_locale' and 'locale'.
                     'fallback_locale' specifies the locale to be used if the requested locale is not supported.
                     'locale' specifies the initial locale to be used.
        """

        if opts is None:
            opts = {}
        self.fallbackLocale = opts.get('fallback_locale', 'en')

        current_locale = self._get_current_locale()

        self.locale = current_locale

        if opts.get('locale', None) is not None:
            self.locale = opts.get('locale', None)

    def _get_current_locale(self):
        """
        Private method to get the current locale of the system.
        It supports English, Japanese, Chinese and Korean languages.

        :return: The current locale of the system in ISO 639-1 format.
        :rtype: str
        """

        try:
            raw_language = locale.getlocale()[0]
            if raw_language is None:
                return 'en'  # default locale

            if '_' in raw_language:
                raw_language = raw_language.split('_')[0]

            current_locale = 'en'

            if raw_language == 'Japanese':
                current_locale = 'ja'
            elif raw_language == 'Chinese':
                current_locale = 'zh'
            elif raw_language == 'Korean':
                current_locale = 'ko'
            elif raw_language == 'English':
                current_locale = 'en'
            elif raw_language == 'French':
                current_locale = 'fr'
            elif raw_language == 'German':
                current_locale = 'de'
            elif raw_language == 'Italian':
                current_locale = 'it'

            return current_locale
        except Exception as e:
            print(f"Error getting locale: {e}")
            return 'en'  # default locale in case of an error

    def get_locale(self):
        """
        Get the locale currently being used.

        :return: The current locale.
        :rtype: str
        """

        return self.locale

    def to_str(self, message):
        """
        Convert a localized message to a string in the current locale.

        :param message: The localized message. It can be a string or a dictionary containing locale-message pairs.
        :return: The message in the current locale if it exists, otherwise the message in the fallback locale.
                 If the message is neither a string nor a dictionary, it returns '(locale_type_error)'.
        :rtype: str
        """
        user_locale = self.locale
        out = ''

        if isinstance(message, dict):
            out = message.get(user_locale)
            if not out:

                if '-' in user_locale:
                    language = user_locale.split('-')[0]
                    out = message.get(language)
                    if not out:
                        out = message.get(self.fallbackLocale)
            return out
        elif isinstance(message, str):
            return message
        else:
            return '(locale_type_error)'
