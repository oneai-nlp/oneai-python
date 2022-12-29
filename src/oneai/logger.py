import logging

PREFIX = "\33[34m●\33[36m▲\33[35m▮\33[0m"

notebook = False
try:
    if get_ipython().__class__.__name__ == "ZMQInteractiveShell":
        notebook = True
except NameError:
    pass


class Formatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.DEBUG:
            if notebook:
                self._style._fmt = f"{PREFIX} %(message)s\r"
            else:
                self._style._fmt = f"\033[K{PREFIX} %(message)s\033[F"
        if record.levelno == logging.DEBUG + 1:
            self._style._fmt = ""
        elif record.levelno == logging.WARNING:
            self._style._fmt = "\33[33m%(message)s\33[0m"
        elif record.levelno == logging.ERROR:
            self._style._fmt = "\33[91m%(message)s\33[0m"
        return super().format(record)


formatter = Formatter()
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger("oneai")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
