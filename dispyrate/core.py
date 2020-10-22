import inspect
import sys
import warnings
from dis import Instruction, get_instructions
from itertools import takewhile
from types import CodeType
from typing import Iterable, List, Mapping, Optional, Tuple, TypeVar

from dispyrate.exceptions import DestructuringError

V = TypeVar('V')

if hasattr(sys, 'ps1'):
    warnings.warn('Destructuring within functions in the interactive prompt is not currently supported.',
                  RuntimeWarning)


# noinspection PyPep8Naming
def D(mapping: Mapping[str, V]) -> Iterable[V]:
    calling_code = get_calling_code()
    unpack, loads = split_instructions(calling_code)
    unpack_index = get_unpack_index(unpack) if unpack is not None else None
    return order_results(mapping, loads, unpack_index)


def get_calling_code() -> CodeType:
    frame = inspect.stack()[2].frame
    context = inspect.getframeinfo(frame).code_context
    return frame.f_code if context is None else compile(context[0].strip(), '', 'single')


def order_results(mapping: Mapping[str, V], loads: Iterable[Instruction], unpack_index: Optional[int]) -> Iterable[V]:
    result = []
    seen = set()
    for index, instruction in enumerate(loads):
        if index != unpack_index:
            name = instruction.argval
            value = get_value(mapping, name)
            seen.add(name)
            result.append(value)

    if unpack_index is not None:
        result[unpack_index:unpack_index] = [value for key, value in mapping.items() if key not in seen]

    return result


def get_value(mapping: Mapping[str, V], name: str) -> V:
    try:
        return mapping[name]

    except KeyError:
        raise DestructuringError(f"Could not find key corresponding to destructuring target '{name}'.") from None

    except TypeError:
        raise DestructuringError(f"Cannot destructure a non-mapping object of type {type(mapping)}.") from None


def split_instructions(code: CodeType) -> Tuple[Instruction, List[Instruction]]:
    instructions = get_instructions(code)
    unpack = None
    loads = []
    for instruction in instructions:
        if instruction.opname == 'UNPACK_EX':
            unpack = instruction
            break

        elif instruction.opname == 'STORE_NAME':
            loads.append(instruction)
            break

    loads.extend(takewhile(lambda ins: ins.opname == 'STORE_NAME', instructions))
    target_count = len(loads)
    if target_count < 2:
        raise DestructuringError(f'Expected at least 2 destructuring targets but got {target_count}.')

    return unpack, loads


def get_unpack_index(unpack_instruction: Instruction) -> int:
    # The low byte of the unpack instruction's argument is the number of values before the starred target.
    # See https://docs.python.org/3/library/dis.html#opcode-UNPACK_EX.
    return unpack_instruction.arg % 256
