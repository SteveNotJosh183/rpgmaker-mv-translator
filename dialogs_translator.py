import argparse
import os
import json
from typing import Any, Generator

import googletrans
from dialog_types import (
    choice_answer_process,
    multiple_choice_process,
    plain_text_process,
)
from translator import Translator


# usage: python dialogs_translator.py --print_neatly --source_lang it --dest_lang en
def new_argpraser() -> argparse.ArgumentParser:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--input_folder", type=str, default="dialogs")
    argparser.add_argument("-sl", "--source_lang", type=str, default="it")
    argparser.add_argument("-dl", "--dest_lang", type=str, default="en")
    argparser.add_argument("-v", "--verbose", action="store_true", default=False)
    argparser.add_argument("-nf", "--no_format", action="store_true", default=False)
    argparser.add_argument("-pn", "--print_neatly", action="store_true", default=False)
    argparser.add_argument("-ml", "--max_len", type=int, default=44)
    argparser.add_argument("-mr", "--max_retries", type=int, default=10)
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


def normal_translate(data: dict, translator: Translator, verbose: bool) -> int:
    to_translate_events = [event for event in data["events"] if event is not None]
    total_translated_dialog = 0
    for event_index, event in enumerate(to_translate_events):
        print("{}/{} events".format(event_index + 1, len(to_translate_events)))
        for dialog in dialogs_query(event):
            code = dialog["code"]
            if code == 102:
                total_translated_dialog += multiple_choice_process(
                    dialog, translator, verbose
                )
            elif code == 401:
                total_translated_dialog += plain_text_process(
                    dialog, translator, verbose
                )
            elif code == 402:
                total_translated_dialog += choice_answer_process(
                    dialog, translator, verbose
                )
    return total_translated_dialog


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
            pass
        elif file_name.startswith("Map"):
            total_translated_dialog += normal_translate(
                data, translator, arguments.verbose
            )
        elif file_name.startswith("CommonEvents"):
            pass
        translated_file_path = os.path.join(translated_folder, file_name)
        dump_json(data, translated_file_path, arguments.no_format)
    print(
        "\ndone! translated in total {} dialog windows".format(total_translated_dialog)
    )


if __name__ == "__main__":
    main()
