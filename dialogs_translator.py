import argparse
import os
import json
from typing import Any, Callable, Generator, Iterable

import googletrans
from dialog_types import (
    choice_answer_process,
    multiple_choice_process,
    neatly_plain_text_process,
    plain_text_process,
)
from translator import Translator

MAX_RETRIES = 10
MAX_LINE_LENGTH = 44


# usage: python dialogs_translator.py --print_neatly --source_lang it --dest_lang en
def new_argpraser() -> argparse.ArgumentParser:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--input_folder", type=str, default="dialogs")
    argparser.add_argument("-sl", "--source_lang", type=str, default="it")
    argparser.add_argument("-dl", "--dest_lang", type=str, default="en")
    argparser.add_argument("-v", "--verbose", action="store_true", default=False)
    argparser.add_argument("-nf", "--no_format", action="store_true", default=False)
    argparser.add_argument("-pn", "--print_neatly", action="store_true", default=False)
    argparser.add_argument("-ml", "--max_len", type=int, default=MAX_LINE_LENGTH)
    argparser.add_argument("-mr", "--max_retries", type=int, default=MAX_RETRIES)
    return argparser


def dump_json(data, file_name, no_format=False) -> None:
    with open(file_name, "w", encoding="utf-8") as file:
        if no_format:
            json.dump(data, file, ensure_ascii=False)
        else:
            json.dump(data, file, indent=4, ensure_ascii=False)


def load_json(file_path: str) -> Any:
    with open(file_path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


def dialogs_query(event: dict) -> Generator[dict, dict, None]:
    for page in event["pages"]:
        for dialog in page["list"]:
            yield dialog


def map_translation(
    data: Iterable,
    translator: Translator,
    translation_type: Callable[[dict, Translator], int],
    *args,
    **kwargs
) -> int:
    to_translate_events = [event for event in data["events"] if event is not None]
    total_translated_dialog = 0
    for event_index, event in enumerate(to_translate_events):
        print("{}/{} events".format(event_index + 1, len(to_translate_events)))
        for dialog in dialogs_query(event):
            total_translated_dialog += translation_type(
                dialog, translator, *args, **kwargs
            )
    return total_translated_dialog


def common_events_translation(
    data: Iterable,
    translator: Translator,
    translation_type: Callable[[dict, Translator], int],
    *args,
    **kwargs
) -> int:
    to_translate_events = [page for page in data if page is not None]
    total_translated_dialog = 0
    for event_index, event in enumerate(to_translate_events):
        print("{}/{} pages".format(event_index + 1, len(to_translate_events)))
        for dialog in event["list"]:
            total_translated_dialog += translation_type(
                dialog, translator, *args, **kwargs
            )
    return total_translated_dialog


def normal_translation(dialog: dict, translator: Translator, *args, **kwargs) -> int:
    code = dialog["code"]
    verbose = kwargs.get("verbose", False)
    if code == 102:
        return multiple_choice_process(dialog, translator, verbose)
    if code == 401:
        return plain_text_process(dialog, translator, verbose)
    if code == 402:
        return choice_answer_process(dialog, translator, verbose)
    return 0


def neatly_translation(dialog: dict, translator: Translator, *args, **kwargs) -> int:
    code = dialog["code"]
    verbose = kwargs.get("verbose", False)
    max_line_length = kwargs.get("max_line_length", MAX_LINE_LENGTH)
    if code == 102:
        return multiple_choice_process(dialog, translator, verbose)
    if code == 401:
        return neatly_plain_text_process(dialog, translator, verbose, max_line_length)
    if code == 402:
        return choice_answer_process(dialog, translator, verbose)
    return 0


def normal_common_event_translation(
    dialog: dict, translator: Translator, *args, **kwargs
) -> int:
    code = dialog["code"]
    verbose = kwargs.get("verbose", False)
    max_line_length = kwargs.get("max_line_length", MAX_LINE_LENGTH)
    if code == 401:
        return neatly_plain_text_process(dialog, translator, verbose, max_line_length)
    return 0


def main() -> None:
    argparser = new_argpraser()
    arguments = argparser.parse_args()
    translator = Translator(
        googletrans.Translator(),
        arguments.source_lang,
        arguments.dest_lang,
        arguments.max_retries,
    )
    translated_folder = arguments.input_folder + "_" + arguments.dest_lang
    total_translated_dialog = 0
    if not os.path.exists(translated_folder):
        os.makedirs(translated_folder)
    for file_name in os.listdir(arguments.input_folder):
        is_traslated_file = os.path.isfile(os.path.join(translated_folder, file_name))
        if is_traslated_file:
            print(
                "Skipped file {} because it has already been translated".format(
                    file_name
                )
            )
            continue
        if not file_name.endswith(".json"):
            continue

        file_path = os.path.join(arguments.input_folder, file_name)
        data = load_json(file_path)
        print("translating file: {}".format(file_name))

        if file_name.startswith("Map") and arguments.print_neatly:
            total_translated_dialog += map_translation(
                data,
                translator,
                neatly_translation,
                verbose=arguments.verbose,
                max_line_length=arguments.max_len,
            )
        elif file_name.startswith("Map"):
            total_translated_dialog += map_translation(
                data,
                translator,
                normal_translation,
                verbose=arguments.verbose,
            )
        elif file_name.startswith("CommonEvents"):
            total_translated_dialog += common_events_translation(
                data,
                translator,
                normal_common_event_translation,
                verbose=arguments.verbose,
                max_line_length=arguments.max_len,
            )
        translated_file_path = os.path.join(translated_folder, file_name)
        dump_json(data, translated_file_path, arguments.no_format)
    print(
        "\ndone! translated in total {} dialog windows".format(total_translated_dialog)
    )


if __name__ == "__main__":
    main()
