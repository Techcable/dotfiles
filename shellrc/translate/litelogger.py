from __future__ import annotations

from enum import Enum
from typing import Final, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from collections import Mapping, LiteralString
    from typing import assert_type


class AnsiColor(Enum):
    RESET_ALL = 0
    NOP = None

    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    GREY = 90

    def __init__(self, code: Optional[int]):
        self.code = code

    def style(self, bold: bool = False) -> AnsiStyle:
        return AnsiStyle(self, bold=bold)


class AnsiStyle:
    __slots__ = "color", "bold"
    color: Optional[AnsiColor]
    bold: bool

    RESET: ClassVar[AnsiStyle]
    NOP: ClassVar[AnsiStyle]

    _BOLD_CODE: ClassVar[int] = 1

    def __init__(self, color, bold: bool = False):
        assert isinstance(color, AnsiColor) or color is None
        if color == AnsiColor.RESET_ALL:
            if bold:
                raise ValueError("RESET_ALL cannot be bold")
        self.color = color
        self.bold = bold

    def encode(self) -> str:
        if self == AnsiStyle.NOP:
            return ""
        AnsiColor._fixup_windows_colors()
        codes = [self.color.value]
        if self.bold:
            codes.append(AnsiStyle._BOLD_CODE)
        return f"\x1b[{';'.join(map(str, codes))}m"

    @staticmethod
    def _fixup_windows_colors():
        try:
            from colorama import just_fix_windows_console
        except (ImportError, AttributeError):
            pass
        else:
            just_fix_windows_console()

    def __repr__(self):
        res = [f"AnsiStyle({self.color!r}"]
        if self.bold:
            res.append(", bold=True")
        res.append(")")
        return "".join(res)

    def __eq__(self, other):
        if isinstance(other, AnsiStyle):
            return self.color == other.color and self.bold == other.bold


AnsiStyle.RESET = AnsiColor.RESET_ALL.style()
AnsiStyle.NOP = AnsiStyle(color=None)

# NOTE: Not exhaustive,
# and don't rely on integer values
class LogLevel(Enum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    # TODO: Is this needed?
    # CRITICAL = 5

    @property
    def default_style(self) -> AnsiStyle:
        colors = (
            AnsiColor.BLUE,  # 0: TRACE
            AnsiColor.CYAN,  # 1: DEBUG
            AnsiColor.NOP,  # 2: INFO, (NOTE: Is green in slog-term)
            AnsiColor.YELLOW,  # 3: WARNING
            AnsiColor.RED,  # 4: ERROR
            AnsiColor.CYAN,  # 5: CRITICAL
        )
        return AnsiStyle(colors[self.value], bold=self.value >= 2)


@dataclass(slots=True)
class LogEvent:
    level: LogLevel
    message: str
    logger: Logger


MessageFormat = Callable[[LogEvent], str]


def defaultMessageFormat(event: LogEvent):
    level = event.level
    logger = event.logger
    colored = logger.colored
    res = []
    if colored:
        level_style = ctx.level.default_style()
        if override := logger.config.override_level_styles:
            level_style = override.get(ctx.level, level_style)
        res.append(level_style)
    res.append(level.name)
    if colored:
        res.append(AnsiStyle.RESET)
    if logger.config.formatted_name:
        if colored:
            res.append(AnsiColor.GREY.style(bold=True))
        res.append("[")
        res.append(logger.config.formatted_name)
        res.append("]")
        if colored:
            res.append(AnsiStyle.RESET)
    res.append(": ")
    res.append(event.message)
    return "".join(
        val.encode() if isinstance(val, AnsiColor) else str(val) for val in res
    )


@dataclass(frozen=True)
class LoggerConfig:
    # The name of the logger (used for nesting)
    name: str = "root"
    formatted_name: str = ""
    level: Optional[LogLevel] = LogLevel.INFO
    message_format: MessageFormat = defaultMessageFormat
    # Force colors. Can be
    # 1. Forced ON: True
    # 2. Forced OFF: False
    # 3. Default: None
    #
    # In default mode, only enabled for terminals
    force_colors: Optional[bool] = None
    override_level_styles: Optional[dict[str, AnsiStyle]] = None


class Logger:
    __slots__ = "level", "_output", "config", "_listeners", "colored", "parent"
    _output: TextIOBase
    level: Final[Optional[LogLevel]]
    config: Final[LoggerConfig]
    parent: Final[Logger]
    colored: bool

    _listeners: set[Callable[[LogEvent], None]]

    def __init__(
        self,
        output: TextIOWriter,
        config: LoggerConfig = LoggerConfig(),
        parent: Optional[Logger] = None,
    ):
        force_set = object.__setattr__  # Workaround immutability
        if config.level is None:
            is_enabled = lambda self, _level: False
        else:
            assert isinstance(config.level, LogLevel)
        if parent is not None:
            assert output is self.parent.output
        force_set(self, "level", config.level)
        force_set(self, "_output", output)
        force_set(self, "config", config)
        force_set(self, "_listeners", set())
        match config.force_colors:
            case bool(force_colors):
                colored = force_colors
            case None:
                colored = output.isatty()
            case _:
                raise TypeError
        force_set(self, "colored", colored)
        force_set(self, "parent", parent)

    def is_enabled(self, level: LogLevel):
        return level.value >= self.level.value if self.level is not None else False

    def trace(self, val: str):
        return self.log(LogLevel.TRACE, val)

    def debug(self, val: str):
        return self.log(LogLevel.DEBUG, val)

    def info(self, val: str):
        return self.log(LogLevel.INFO, val)

    def warning(self, val: str):
        return self.log(LogLevel.WARNING, val)

    def error(self, val: str):
        return self.log(LogLevel.ERROR, val)

    def register_listener(self, listener: LogListener):
        if TYPE_CHECKING:
            assert_type(listener, Callable)
        assert callable(listener)
        assert listener not in self._listeners, "Duplicate listener"
        self._listeners.add(listener)

    def unregister_listener(self, listener: LogListener):
        try:
            self._listeners.remove(listener)
        except KeyError:
            raise AssertionError("Listener not registered") from None

    def log(self, level: LogLevel, val: str):
        if not self.is_enabled(level):
            return
        # Past here, everything is dwarfed by IO
        self._fire_event(
            LogEvent(
                level=level,
                logger=self,
                message=val,
            )
        )

    def _fire_event(self, event: LogEvent):
        for listener in self._listeners:
            listener(event)
        if self.parent is not None:
            return self.parent._fire_event(event)
        # NOTE: Prefer event.logger.config over self.config, because
        # we may be printing child logger's event
        config = event.logger.config
        formatted = config.message_format(event)
        # TODO: Thread safety?
        self._output.write(formatted + "\n")

    def __setattr__(self, attr, val):
        # TODO: Is this worth the complexity
        raise NotImplementedError(f"Cannot modify frozen attrbute: Logger.{attr}")

    def __repr__(self) -> str:
        return f"<litelogger {self.config.name!r} output={getattr(self.output, 'name', repr(self.output))}>"

    def close(self):
        if self.parent is not None:
            # TODO: Refcounting or something?
            assert self.parent.output is self.output
        else:
            self.output.close()
