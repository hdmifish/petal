from . import core


class CommandsUtil(core.Commands):
    def echo(self, text, *a, src, **kw):
        print(text)

    def echo2(self, text, *a, loud=False, src, **kw):
        if loud:
            print(text.upper())
        else:
            print(text)


# Keep the actual classname unique from this common identifier
# Might make debugging nicer
CommandModule = CommandsUtil
