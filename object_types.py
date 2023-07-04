from dialog_types import reformat_translated_text, translate, auto_wrap_line
from translator import Translator
from pymonad.maybe import Maybe


MAX_LINE_LENGTH = 55


def is_key_translatable(key: str, dictionary: dict) -> bool:
    return len(dictionary.get(key, "")) > 0


def name_process(element: dict, translator: Translator, verbose: bool = False) -> int:
    text = element["name"]
    translated_text: Maybe = Maybe.insert(text).then(translate(translator))
    if translated_text.is_nothing():
        return 0
    if verbose:
        print("Name: {} -> {}".format(text, translated_text.value))
    formatted_text: Maybe = translated_text.then(reformat_translated_text(text))
    if formatted_text.is_nothing():
        return 0
    element["name"] = formatted_text.value
    return 1


def description_process(
    element: dict, translator: Translator, max_line_length: int, verbose: bool = False
) -> int:
    text = element["description"]
    translated_text: Maybe = Maybe.insert(text).then(translate(translator))
    if translated_text.is_nothing():
        return 0
    if verbose:
        print("Description: {} -> {}".format(text, translated_text.value))
    formatted_text: Maybe = translated_text.then(reformat_translated_text(text)).then(
        auto_wrap_line(max_line_length)
    )
    if formatted_text.is_nothing():
        return 0
    element["description"] = formatted_text.value
    return 1


def profile_process(
    element: dict, translator: Translator, max_line_length: int, verbose: bool = False
) -> int:
    text = element["profile"]
    translated_text: Maybe = Maybe.insert(text).then(translate(translator))
    if translated_text.is_nothing():
        return 0
    if verbose:
        print("Profile: {} -> {}".format(text, translated_text.value))
    formatted_text: Maybe = translated_text.then(reformat_translated_text(text)).then(
        auto_wrap_line(max_line_length)
    )
    if formatted_text.is_nothing():
        return 0
    element["profile"] = formatted_text.value
    return 1


def message_process(
    element: dict, key: str, translator: Translator, verbose: bool = False
) -> int:
    text = element[key]
    translated_text: Maybe = Maybe.insert(text).then(translate(translator))
    if translated_text.is_nothing():
        return 0
    if verbose:
        print("{}: {} -> {}".format(key.capitalize(), text, translated_text.value))
    formatted_text: Maybe = translated_text.then(reformat_translated_text(text))
    if formatted_text.is_nothing():
        return 0
    element[key] = formatted_text.value
    return 1


def normal_object_translation(
    element: dict, translator: Translator, *args, **kwargs
) -> int:
    verbose = kwargs.get("verbose", False)
    max_line_length = kwargs.get("max_line_length", MAX_LINE_LENGTH)
    total_translated_object = 0
    if is_key_translatable("name", element):
        total_translated_object += name_process(element, translator, verbose)
    if is_key_translatable("description", element):
        total_translated_object += description_process(
            element, translator, max_line_length, verbose
        )
    if is_key_translatable("profile", element):
        total_translated_object += profile_process(
            element, translator, max_line_length, verbose
        )
    for number in range(1, 5):
        message = "message" + str(number)
        if is_key_translatable(message, element):
            total_translated_object += message_process(
                element, message, translator, verbose
            )
    return total_translated_object
