import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from cost_janitor import get_tag_dict, is_protected


def test_get_tag_dict():

    tags = [
        {"Key": "Project", "Value": "NimbusKart"},
        {"Key": "Owner", "Value": "Priyansi"}
    ]

    result = get_tag_dict(tags)

    assert result["Project"] == "NimbusKart"
    assert result["Owner"] == "Priyansi"


def test_is_protected_true():

    tags = {
        "Protected": "true"
    }

    assert is_protected(tags) is True


def test_is_protected_false():

    tags = {}

    assert is_protected(tags) is False
