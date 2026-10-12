"""Issue messages of the command line (U-M5a): what `embodic-cli` reports apart from the issues of the other modules."""

from collections.abc import Mapping

MESSAGES: Mapping[str, str] = {
    "INVALID_CLI_USAGE": "The command line is not valid; run embodic-cli --help to see the commands and options.",
    "INVALID_CLI_OUTPUT_UNWRITABLE": (
        "The output file cannot be written; check that its folder exists and that you may write there."
    ),
    "INTERNAL_CLI_FAILED": "The command stopped with an internal error; the traceback is attached.",
}
