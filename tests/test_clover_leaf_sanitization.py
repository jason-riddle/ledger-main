from __future__ import annotations

import beanout.clover_leaf as clover_leaf


def test_clover_leaf_sanitizes_newlines_in_strings() -> None:
    payee = "Halo Locksmith LLC\nJuan Ramirez"
    narration = "Memo: Lock change\nLandlord compliance"

    entries = clover_leaf.render_clover_leaf_json_text(
        """
{"rows":[{"rowTypeID":3,"data":{"datePosted":"2025-11-05","accountNumber":"6405","accountName":"Lock Change","description":"Lock change\\nLandlord compliance","payeePayerName":"Halo Locksmith LLC\\nJuan Ramirez","propertyAddress":"206 Hoover Ave","increase":null,"decrease":"334.49"}}]}
""".strip()
    )

    assert payee not in entries
    assert narration not in entries
    assert payee.replace("\n", " ") in entries
    assert narration.replace("\n", " ") in entries
