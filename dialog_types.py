import re
from typing import Optional
from pymonad.maybe import Maybe, Nothing
from pymonad.tools import curry
from print_neatly import print_neatly

from translator import Translator

PATTERN = r"\\evalText<<.+>>|\\.+?[\]}>]|\\\S+|<\w+>"


def plain_text_process(dialog: dict, translator: Translator, verbose: bool) -> int:
    translated_text: Maybe = (
        Maybe.insert(dialog)
        .then(extract_plain_text)
        .then(validate_plain_text)
        .then(keep_text_code_translate(translator))
    )
    if translated_text.is_nothing():
        print("Anomaly plain text: {}".format(extract_plain_text(dialog)))
        return 0
    if verbose:
        print(
            "Plain text(401): {} -> {}".format(
                extract_plain_text(dialog), translated_text.value
            )
        )
    dialog["parameters"][0] = translated_text.then(
        reformat_translated_text(extract_plain_text(dialog))
    ).maybe(extract_plain_text(dialog), lambda x: x)
    return 1


def multiple_choice_process(dialog: dict, translator: Translator, verbose: bool) -> int:
    translated_dialog_number = 0
    for index, choice in enumerate(extract_choice_list(dialog)):
        translated_text: Maybe = Maybe.insert(choice).then(translate(translator))
        if translated_text.is_nothing():
            print("Anomaly choices: {}".format(choice))
            continue
        if verbose:
            print("Choice(102): {} -> {}".format(choice, translated_text.value))
        dialog["parameters"][0][index] = translated_text.then(
            reformat_translated_text(choice)
        ).maybe(choice, lambda x: x)
        translated_dialog_number += 1
    return translated_dialog_number


def choice_answer_process(dialog: dict, translator: Translator, verbose: bool) -> int:
    validated_dialog: Maybe = Maybe.insert(dialog).then(validate_choice_answer)
    if validated_dialog.is_nothing():
        print(
            "Anomaly choices (answer) - Unexpected 402 Code: {}".format(
                dialog["parameters"]
            )
        )
        return 0
    translated_text: Maybe = validated_dialog.then(extract_choice_answer).then(
        translate(translator)
    )
    if translated_text.is_nothing():
        print("Anomaly choices (answer): {}".format(extract_choice_answer(dialog)))
        return 0
    if verbose:
        print(
            "Choice answer(402): {} -> {}".format(
                extract_choice_answer(dialog), translated_text.value
            )
        )
    dialog["parameters"][1] = translated_text.then(
        reformat_translated_text(extract_choice_answer(dialog))
    ).maybe(extract_plain_text(dialog), lambda x: x)
    return 1


def neatly_plain_text_process(
    dialog: dict, translator: Translator, verbose: bool, max_line_length: int
) -> int:
    translated_text: Maybe = (
        Maybe.insert(dialog)
        .then(extract_plain_text)
        .then(validate_plain_text)
        .then(keep_text_code_translate(translator))
    )
    if translated_text.is_nothing():
        print("Anomaly plain text: {}".format(extract_plain_text(dialog)))
        return 0
    if verbose:
        print(
            "Plain text(401): {} -> {}".format(
                extract_plain_text(dialog), translated_text.value
            )
        )
    dialog["parameters"][0] = (
        translated_text.then(reformat_translated_text(extract_plain_text(dialog)))
        .then(auto_wrap_line(max_line_length))
        .maybe(extract_plain_text(dialog), lambda x: x)
    )
    return 1


def extract_choice_list(dialog: dict) -> list[str]:
    return dialog["parameters"][0]


def extract_plain_text(dialog: dict) -> Optional[str]:
    return dialog["parameters"][0]


def extract_choice_answer(dialog: dict) -> Optional[str]:
    return dialog["parameters"][1]


def validate_choice_answer(dialog: dict) -> Optional[dict]:
    if len(dialog["parameters"]) != 2:
        return Nothing
    if not dialog["parameters"][1]:
        return Nothing
    return dialog


def validate_plain_text(text: str) -> Optional[str]:
    if not text:
        return Nothing
    return text


@curry(2)
def auto_wrap_line(max_line_length: int, text: str) -> str:
    try:
        return "\n".join(print_neatly(text.replace("\n", " "), max_line_length))
    except Exception:
        return text


@curry(2)
def keep_text_code_translate(translator: Translator, text: str) -> Optional[str]:
    text_codes = get_text_codes(text) + [""]
    splitted_texts = split_by_text_code(text)
    translated_splitted_texts = translator.try_translate_sequence(splitted_texts)
    if translated_splitted_texts is None:
        return Nothing
    rejoin_text_list = []
    for text_section, code in zip(translated_splitted_texts, text_codes):
        rejoin_text_list.append("" if text_section is None else text_section)
        rejoin_text_list.append(code)
    return " ".join(rejoin_text_list)


@curry(2)
def translate(translator: Translator, text: str) -> Optional[str]:
    return translator.try_translate(text)


@curry(2)
def reformat_translated_text(original: str, translated: str) -> str:
    if (not original) or original is None:
        return translated
    if original.strip()[0].islower() and translated.strip()[0].isalpha():
        return translated[0].lower() + translated[1:]
    if original.strip()[0].isupper() and translated.strip()[0].isalpha():
        return translated[0].upper() + translated[1:]
    return translated


def get_text_codes(text: str) -> list[str]:
    return re.findall(PATTERN, text)


def split_by_text_code(text: str) -> list[str]:
    return re.split(PATTERN, text)
