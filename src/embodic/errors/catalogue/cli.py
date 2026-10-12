"""Issue messages of the command line (U-M5a): what `embodic-cli` reports apart from the issues of the other modules."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "INVALID_CLI_USAGE": "The command line is not valid; run embodic-cli --help to see the commands and options.",
    "INVALID_CLI_OUTPUT_UNWRITABLE": (
        "The output file cannot be written; check that its folder exists and that you may write there."
    ),
    "DRC_CLI_EXPORT_REFUSED": (
        "Nothing was written. Run the command again with --allow-drc-errors to write the files although the design "
        "rule check failed."
    ),
    "DRC_CLI_EXPORT_FORCED": (
        "The design rule check failed and the files were written because --allow-drc-errors was given."
    ),
    "INTERNAL_CLI_FAILED": "The command stopped with an internal error; the traceback is attached.",
}
