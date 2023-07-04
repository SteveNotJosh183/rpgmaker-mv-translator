import argparse
import json
import os
from typing import Any, Callable

import googletrans

from object_types import normal_object_translation
from translator import Translator


# usage: python objects_translator.py --source_lang it --dest_lang en
def new_argpraser() -> argparse.ArgumentParser:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-i", "--input_folder", type=str, default="objects")
    argparser.add_argument("-sl", "--source_lang", type=str, default="it")
    argparser.add_argument("-dl", "--dest_lang", type=str, default="en")
    argparser.add_argument("-v", "--verbose", action="store_true", default=False)
    argparser.add_argument("-nf", "--no_format", action="store_true", default=False)
    argparser.add_argument("-ml", "--max_len", type=int, default=55)
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


def object_translation(
    data: dict,
    translator: Translator,
    translation_type: Callable[[dict, Translator], int],
    *args,
    **kwargs
) -> int:
    total_translated_object = 0
    to_translated_objects = [element for element in data if element is not None]

    for index, element in enumerate(to_translated_objects):
        if element is None:
            continue
        print("{}/{} objects".format(index + 1, len(to_translated_objects)))
        total_translated_object += translation_type(
            element, translator, *args, **kwargs
        )

    return total_translated_object


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
    translatable_file_names = [
        "Actors.json",
        "Armors.json",
        "Weapons.json",
        "Items.json",
        "Skills.json",
        "Enemies.json",
        "MapInfos.json",
        "Classes.json",
        "States.json",
    ]
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
        if file_name not in translatable_file_names:
            continue

        file_path = os.path.join(arguments.input_folder, file_name)
        data = load_json(file_path)
        print("translating file: {}".format(file_name))

        total_translated_dialog += object_translation(
            data,
            translator,
            normal_object_translation,
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
