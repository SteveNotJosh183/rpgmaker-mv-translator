from typing import Optional
from pymonad.maybe import Maybe
from pymonad.tools import curry

from translator import Translator


def plain_text_process(dialog: dict, translator: Translator, verbose: bool) -> int:
    translated_text: Maybe = (
        Maybe.insert(dialog).then(extract_plain_text).then(translate(translator))
    )
    if translated_text.is_nothing():
        print("Anomaly plain text: {}".format(extract_plain_text(dialog)))
        return 0
    if verbose:
        print("Plain text(401): {} -> {}".format(*translator.get_last_translation()))
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
            print("Choice(102): {} -> {}".format(*translator.get_last_translation()))
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
    translated_text: Maybe = validated_dialog.then(extraxt_choice_answer).then(
        translate(translator)
    )
    if translated_text.is_nothing():
        print("Anomaly choices (answer): {}".format(extraxt_choice_answer(dialog)))
        return 0
    if verbose:
        print("Choice answer(402): {} -> {}".format(*translator.get_last_translation()))
    dialog["parameters"][1] = translated_text.then(
        reformat_translated_text(extraxt_choice_answer(dialog))
    ).maybe(extract_plain_text(dialog), lambda x: x)
    return 1


def extract_choice_list(dialog: dict) -> list[str]:
    return dialog["parameters"][0]


def extract_plain_text(dialog: dict) -> Optional[str]:
    return dialog["parameters"][0]


def extraxt_choice_answer(dialog: dict) -> Optional[str]:
    return dialog["parameters"][1]


def validate_choice_answer(dialog: dict) -> Optional[dict]:
    if len(dialog["parameters"]) != 2:
        return
    if not dialog["parameters"][1]:
        return
    return dialog


@curry(2)
def translate(text: str, translator: Translator) -> Optional[str]:
    return translator.try_translate(text)


@curry(2)
def reformat_translated_text(translated: str, original: str) -> str:
    if original[0].isalpha() and translated[0].isalpha and not original[0].isupper():
        return translated[0].lower() + translated[1:]
    return translated
