#!/usr/bin/env python
import json
import click
import logging
import os
import re
import zipfile
from functools import cache
from glob import glob

from adobe.pdfservices.operation.auth.credentials import Credentials
from adobe.pdfservices.operation.exception.exceptions import (
    ServiceApiException,
    ServiceUsageException,
    SdkException,
)
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_pdf_options import (
    ExtractPDFOptions,
)
from adobe.pdfservices.operation.pdfops.options.extractpdf.extract_element_type import (
    ExtractElementType,
)
from adobe.pdfservices.operation.execution_context import ExecutionContext
from adobe.pdfservices.operation.io.file_ref import FileRef
from adobe.pdfservices.operation.pdfops.extract_pdf_operation import ExtractPDFOperation
from tqdm import tqdm

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

ITEMS_PATH_TO_IGNORE = [
    r"^\/\/Document\/Sect/.*",
    r"^\/\/Document\/Sect\[2\]\/H1",
    r"^\/\/Document\/.*Table.*",
    r"\/\/Document\/Title",
    r"^\/\/Document\/.*?P\[.*?\]\/Sub.*",
    r"^\/\/Document\/.*\/L.*\/LI.*\/Lbl",
    r".*[fF]igure.*",
]

ITEMS_CONTENT_TO_IGNORE = [
    r"^\d{3}\/\d{4}-\w{3} $",  # Document code
    r".*?Participantes do (Listado|Balcão).*?B3",  # Recipents
    r"Ref\.:.*",  # Document reference
    r"(^\w*@.*|www\.\w*)\.com\.br$", # dangling websites or e-mail addresses
    r"^[Ee]sclarecimento.*(\(\d{2}\).{1,4}\d{4}\-\d{4}|e-mail).*",  # Final paragraph
]

ITEMS_CONTENT_TO_REPLACE = [
    r"[\u2022\u2023\u25E6\u2043\u2219] {0,1}",
]

REFERENCES_PATTERN = r"(.*\/)(StyleSpan\/Reference)"
ATTACHMENTS_PATTERN = (
    r"Anexo.*do (OFÍCIO CIRCULAR|COMUNICADO EXTERNO) \d{3}\/\d{4}-.{0,4}\w{3}"
)
PARAGRAPH_SPANS_PATTERN = r"(.*\/)(ParagraphSpan)"
BSM_COMMUNICATIONS_PATTERN = (
    r"Esclarecimentos adicionais poderão ser obtidos com a BSM.*"
)


@click.group()
@click.pass_context
def cli(ctx):
    pass


@cache
def _get_credentials():
    return (
        Credentials.service_principal_credentials_builder()
        .with_client_id(os.getenv("PDF_SERVICES_CLIENT_ID"))
        .with_client_secret(os.getenv("PDF_SERVICES_CLIENT_SECRET"))
        .build()
    )


def _convert_pdf_file_to_json(
    input_file, base_input_path, output_file, base_output_path
):
    try:
        # Initial setup, create credentials instance.
        credentials = _get_credentials()

        # Create an ExecutionContext using credentials and create a new operation instance.
        execution_context = ExecutionContext.create(credentials)
        extract_pdf_operation = ExtractPDFOperation.create_new()

        # Set operation input from a source file.
        source = FileRef.create_from_local_file(base_input_path + input_file)
        extract_pdf_operation.set_input(source)

        # Build ExtractPDF options and set them into the operation
        extract_pdf_options: ExtractPDFOptions = (
            ExtractPDFOptions.builder()
            .with_element_to_extract(ExtractElementType.TEXT)
            .build()
        )
        extract_pdf_operation.set_options(extract_pdf_options)

        # Execute the operation.
        logging.info("Extracting PDF content...")
        result: FileRef = extract_pdf_operation.execute(execution_context)

        # Save the result to the specified location.
        logging.info(f"Saving extracted content on {base_output_path + output_file}...")
        result.save_as(base_output_path + output_file)

        # Unzip the generated file
        file_to_unpack = base_output_path + output_file
        dest_filename = input_file.replace(".pdf", ".json")
        zip_file_name = "structuredData.json"

        logging.info(f"Unzipping file {file_to_unpack}...")
        with zipfile.ZipFile(file_to_unpack, "r") as file:
            file.getinfo(zip_file_name).filename = dest_filename
            file.extract(zip_file_name, base_output_path)

        os.remove(file_to_unpack)

    except (ServiceApiException, ServiceUsageException, SdkException) as e:
        logging.exception(
            f"Exception encountered while executing operation for file {input_file}: \n",
            e,
        )
        raise e


@cli.command("pdf-to-json")
@click.option(
    "--input-path",
    "-i",
    help="Fully qualified path if the input directory containing the PDFs to convert.",
)
@click.option(
    "--output-path",
    "-o",
    help="Fully qualified path if the output directory to hold the structured jsons.",
)
def convert_pdf_files_to_json(input_path, output_path):
    file_list = set(item.replace(".pdf", "") for item in os.listdir(input_path))
    dest_file_list = set(item.replace(".json", "") for item in os.listdir(output_path))

    files_to_process = file_list - dest_file_list
    logging.info(f"Found {len(files_to_process)} PDFs to convert!")

    for file in tqdm(files_to_process):
        input_file_name = file + ".pdf"
        output_file_name = file + ".zip"
        logging.info(f"Processing file {input_file_name}...")

        try:
            _convert_pdf_file_to_json(
                input_file=input_file_name,
                base_input_path=input_path,
                output_file=output_file_name,
                base_output_path=output_path,
            )
        except ServiceUsageException as e:
            logging.exception(
                "API monthly limit reached!",
                e,
            )
            break

    logging.info("Finished conversion!!!")


def _apply_patterns(text, patterns):
    # Define a function to apply re.sub() with a specific pattern
    def replace_pattern(pattern):
        return re.sub(pattern, "", text)

    # Use map to apply the replace_pattern function to each pattern in the list
    modified_text_list = map(replace_pattern, patterns)

    # Join the modified_text_list to get the final result
    final_result = "".join(modified_text_list)

    return final_result


def _store_paragraph_spans(span_content, spans_dict, idx, text):
    reference_element = span_content.group(0)

    if reference_element not in spans_dict.keys():
        spans_dict[reference_element] = dict()
        spans_dict[reference_element]["idx"] = idx
        spans_dict[reference_element]["text"] = text
    else:
        spans_dict[reference_element]["text"] += text


def _process_file_content(file_contents):
    references = dict()
    paragraph_spans = dict()

    processed_content = []
    idx = 0

    for item in file_contents.get("elements"):
        # We force-pass the first element (in this case) we
        # won't want it
        if idx == 0:
            idx += 1
            continue
        path = item.get("Path")
        text = item.get("Text", "")

        should_exclude_paths = any(
            re.match(pattern, path) for pattern in ITEMS_PATH_TO_IGNORE
        )
        should_exclude_texts = any(
            re.match(pattern, text) for pattern in ITEMS_CONTENT_TO_IGNORE
        )

        is_reference = re.match(REFERENCES_PATTERN, path)
        is_attachment = re.match(ATTACHMENTS_PATTERN, text)
        is_paragraph_span = re.match(PARAGRAPH_SPANS_PATTERN, path)
        is_bsm_communication = re.match(BSM_COMMUNICATIONS_PATTERN, text)

        # Verifications BEFORE the actual processing
        # If we don't want that element we go to the next element
        if should_exclude_paths or should_exclude_texts:
            continue

        # If we reach the attachment we break the loop to process
        # the next document
        if is_attachment:
            break

        # If it is a paragraph span, we store it to recompose the entire paragraph
        # later on
        if is_paragraph_span:
            _store_paragraph_spans(is_paragraph_span, paragraph_spans, idx, text)
            continue

        # Processing
        text = _apply_patterns(text, ITEMS_CONTENT_TO_REPLACE)
        text = re.sub(r" \. ", ". ", text)

        # Post-processing checks
        # References are how Adobe PDF Extract interpret entities
        # such as URLs and e-mail addresses
        # We are storing but currently not using them
        if is_reference:
            reference_path = is_reference.group(1)
            references[reference_path] = text
            continue

        if is_bsm_communication:
            processed_content.append((idx, text))
            break

        processed_content.append((idx, text))
        idx += 1

    return processed_content, paragraph_spans


def _force_signatures_removal(processed_content):
    last_text_with_period_idx = 0
    for i in range(len(processed_content)):
        item = processed_content[i][1]

        if item.endswith(". "):
            last_text_with_period_idx = i

    return processed_content[: last_text_with_period_idx + 1]


def _process_paragraph_spans(paragraph_spans, processed_content):
    resulting_content = processed_content.copy()

    for _, item in paragraph_spans.items():
        idx = item.get("idx")
        content = item.get("text")

        resulting_content.insert(idx - 1, (idx, content))

    return resulting_content


def _tuples_to_list(processed_content):
    return [item for _, item in processed_content]


def _process_periods(text):
    # Forcing to always have a period
    periods_count = text.count(". ")
    text = text.strip()
    if len(text) == 0:
        return ""

    text = text[0].upper() + text[1:]

    # Text ending with ; or :
    if periods_count == 0 and (text.endswith(";") or text.endswith(":")):
        text = text[:-1] + ". "

    # Text ending with nothing
    elif periods_count == 0 and not (text.endswith(";") or text.endswith(":")):
        try:
            text = text + ". "
        except:
            pass
    elif periods_count != 0 and not (text.endswith(";") or text.endswith(":") or text.endswith(".")):
        text = text + ". "
    elif not (text.endswith(";") or text.endswith(":") or text.endswith(".") or text.endswith("?") or text.endswith("!")):
        text += ". "

    if text.endswith("."):
        text = text + " "

    return text


def _process_dangling_entries(text):
    return text.replace(" , ", " ").replace(" ; ", " ")


def _process_multiple_whitespaces(text):
    return re.sub(r"\s{2,}", " ", text)


def _compose_final_text(processed_content):
    processed_periods = map(_process_periods, processed_content)
    processed_dangling_entries = map(_process_dangling_entries, processed_periods)
    processed_multiple_whitepaces = map(
        _process_multiple_whitespaces, processed_dangling_entries
    )

    return "".join(list(processed_multiple_whitepaces)).strip()


def _convert_json_file_to_txt(input_file, output_path):
    base_file_name = input_file.split("/")[-1].replace(".json", ".txt")

    with open(input_file, "r") as f:
        file = f.read()
        contents = json.loads(file)

    processed_content, paragraph_spans = _process_file_content(contents)
    cleaned_content = _force_signatures_removal(processed_content)
    processed_paragraph_spans = _process_paragraph_spans(
        paragraph_spans, cleaned_content
    )
    processed_content_list = _tuples_to_list(processed_paragraph_spans)
    final_content = _compose_final_text(processed_content_list)

    with open(f"{output_path}{base_file_name}", "w") as f:
        file = f.write(final_content)


@cli.command("json-to-txt")
@click.option(
    "--input-path",
    "-i",
    help="Fully qualified path if the input directory containing the JSONs to convert.",
)
@click.option(
    "--output-path",
    "-o",
    help="Fully qualified path if the output directory to hold the txts.",
)
def convert_json_files_to_txt(input_path, output_path):
    path = os.path.join(input_path, "*.json")
    file_list = glob(path)
    logging.info(f"Found {len(file_list)} JSONs to parse!")

    for file in tqdm(file_list):
        logging.info(f"Processing file {file}...")
        _convert_json_file_to_txt(
            input_file=file, output_path=output_path
        )

    logging.info("Finished conversion!!!")


if __name__ == "__main__":
    cli()
