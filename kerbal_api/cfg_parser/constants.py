import re


# Localization tags of the form "#autoLOC_123456" are generally followed by a comment
# that may include the same localization tag and an "=" sign, followed by the English text.
# This pattern matches localized values, extracting:
# - the tag value, under group name "tag"
# - the English text, under group name "english"
localization_pattern = re.compile(
    r"(?P<tag>#autoLOC_\d+)\s+//(?:\s*\1\s*=)?(?P<english>.*)"
)

comment_sequence = "//"
