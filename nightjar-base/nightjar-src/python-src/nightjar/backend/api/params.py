
from typing import Sequence, Iterable, Tuple, Dict, Optional, Generic, TypeVar, List, Type, Any, Callable, Union, Text, cast
import os
import argparse

T = TypeVar('T')
ArgType = Union[str, int, bool]
ArgTypeT = TypeVar('ArgTypeT', str, int, bool)


class ParamDef(Generic[ArgTypeT]):
    __slots__ = (
        'name', 'env_name', 'arg_names', 'help_text', 'default_value', 'required', 'var_type', 'parse_var_type'
    )
    default_value: Optional[ArgTypeT]

    def __init__(
            self,
            name: str,
            env_name: str,
            arg_names: Sequence[str],
            help_text: str,
            default_value: Optional[ArgTypeT],
            var_type: Type[ArgType],
            required: bool = True,
    ) -> None:
        assert len(arg_names) > 0 and not isinstance(arg_names, str)
        self.name = name
        self.env_name = env_name
        self.arg_names = tuple(arg_names)
        self.help_text = help_text
        self.default_value = default_value
        self.required = required
        self.var_type = var_type
        self.parse_var_type = cast(Union[Callable[[Text], T], Callable[[str], T]], var_type)
        assert var_type in (int, str, bool)

    @property
    def store_type(self) -> str:
        if self.var_type == bool:
            return 'store_true'
        return 'store'

    def parse_value(self, value: Optional[str]) -> Optional[ArgTypeT]:
        if value is None:
            return self.default_value
        if self.var_type == bool:
            return cast(
                ArgTypeT,
                value.lower().strip() in ('on', 'yes', 'true', 'active', 'activated', 'enable', 'enabled', '1')
            )
        if self.var_type == int:
            return cast(ArgTypeT, int(value))
        assert self.var_type == str
        return cast(ArgTypeT, value)

    def get_value(self, params: Dict[str, Any]) -> Optional[ArgTypeT]:
        value = params.get(self.name, None)
        if value is None:
            ret = self.default_value
            if ret is None and self.required:
                raise ValueError('Did not specify environment variable {0}'.format(self.env_name))
            return ret
        if isinstance(value, cast(type, self.var_type)):
            return cast(ArgTypeT, value)
        if isinstance(value, str):
            return self.parse_value(value)
        raise ValueError('Expected {0} to have a value of type {1}, but found `{2}`'.format(
            self.env_name, self.var_type, value
        ))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ParamDef):
            return False
        return (
            self.name == other.name
            and self.env_name == other.env_name
            and self.arg_names == other.arg_names
            and self.help_text == other.help_text
            and self.default_value == other.default_value
            and self.required == other.required
            and self.var_type == other.var_type
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return (
                hash(self.name) + hash(self.env_name) +
                hash(self.arg_names) + hash(self.help_text) +
                hash(self.default_value) + hash(self.required) +
                hash(self.var_type)
        )


ParamValues = Dict[str, ArgType]


def parse_env_values(params: Sequence[ParamDef]) -> ParamValues:
    """Used to parse the parameters for an implementation, when the
    implementation is known beforehand."""
    ret = {}
    for param in params:
        value = param.parse_value(os.environ.get(param.env_name))
        if value is not None:
            ret[param.name] = value
    return ret


class ImplementationParameters:
    __slots__ = ('name', 'description', 'params', 'aliases')

    def __init__(self, name: str, aliases: Iterable[str], description: str, params: Sequence[ParamDef]) -> None:
        self.name = name
        self.description = description
        self.params = tuple(params)
        self.aliases = tuple({name, *aliases})

    def parse_env_values(self) -> ParamValues:
        return parse_env_values(self.params)


def setup_argparse(
        parser: argparse.ArgumentParser,
        api_name: str,
        api_help: str,
        impl_dest: str,
        impl_params: Iterable[ImplementationParameters]
) -> argparse.ArgumentParser:
    """
    Creates groups of arguments, one per implementation, along with an
    argument to declare which implementation is used.

    This should use "subparsers", but a parser cannot have multiple
    subparsers.
    """
    choices: List[str] = []
    for impl in impl_params:
        choices.extend(impl.aliases)
    parser.add_argument(
        '--' + api_name,
        help=api_help,
        required=True,
        choices=choices,
        dest=impl_dest,
    )
    for impl in impl_params:
        group = parser.add_argument_group(title=impl.name, description=impl.description)
        for param in impl.params:
            help_text = param.help_text
            if param.env_name:
                help_text += '  Defaults to env value {0}'.format(param.env_name)
            group.add_argument(
                *[('--' + n) for n in param.arg_names],
                required=False,  # NOTE!  Never required, because other implementations may not need this.
                dest=param.name,
                action=param.store_type,
                help=help_text,
                type=param.var_type,
                default=os.environ.get(param.env_name, param.default_value),
            )
    return parser


def pull_argparse(
        results: argparse.Namespace, impl_dest: str, impl_params: Iterable[ImplementationParameters]
) -> Optional[Tuple[ImplementationParameters, ParamValues]]:
    if not hasattr(results, impl_dest):
        return None
    impl_name = getattr(results, impl_dest)
    for impl_param in impl_params:
        if impl_name in impl_param.aliases:
            res: ParamValues = {}
            for param in impl_param.params:
                if hasattr(results, param.name):
                    res[param.name] = getattr(results, param.name)
            return impl_param, res
    return None
