# cards.py
from typing import Dict, List
from botbuilder.schema import Attachment, AttachmentLayoutTypes, Activity, ActivityTypes

def build_app_card(app_row: Dict) -> Attachment:
    """
    app_row: { id, app_name, install_url, versions: [..] }
    """
    versions = app_row.get("versions", ["latest"])
    default_version = versions[0] if versions else "latest"

    card = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            { "type": "TextBlock", "text": app_row["app_name"].title(), "weight": "Bolder", "size": "Medium" },
            { "type": "TextBlock", "text": (app_row.get("install_url") or "No install URL provided"), "isSubtle": True, "wrap": True },
            {
                "type": "Input.ChoiceSet",
                "id": "version",
                "label": "Version",
                "style": "compact",
                "value": default_version,
                "choices": [ { "title": v, "value": v } for v in versions ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Install",
                "data": {
                    "intent": "install_app",
                    "app": app_row["app_name"]
                }
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card
    )

def build_catalog_activity(apps: List[Dict]) -> Activity:
    attachments = [build_app_card(a) for a in apps]
    return Activity(
        type=ActivityTypes.message,
        attachments=attachments,
        attachment_layout=AttachmentLayoutTypes.carousel  # shows cards side-by-side
    )
