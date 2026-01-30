"""
Notification node for the LangGraph workflow
"""
import logging
from typing import Dict, Any
from app.graph.state import GraphState
from app.integrations.twilio.client import TwilioClient

logger = logging.getLogger(__name__)


class NotificationNode:
    """Node responsible for sending notifications"""

    def __init__(self):
        self.twilio_client = TwilioClient()

    def process(self, state: GraphState) -> Dict[str, Any]:
        """Process the notification step"""
        try:
            if not state.needs_notification:
                logger.info("No notification needed")
                return state.dict()

            notification_message = self._generate_notification_message(state)

            # Send WhatsApp notification
            success = self.twilio_client.send_notification(
                message=notification_message,
                notification_type=state.notification_type
            )

            if success:
                logger.info(f"Notification sent: {state.notification_type}")
                state.notification_message = notification_message
            else:
                logger.error("Failed to send notification")
                state.notification_message = "Failed to send notification"

            return state.dict()

        except Exception as e:
            logger.error(f"Notification failed: {e}")
            state.notification_message = f"Notification error: {str(e)}"
            return state.dict()

    def _generate_notification_message(self, state: GraphState) -> str:
        """Generate appropriate notification message"""
        if state.notification_type == "conflict":
            return f"""🚨 Evidence Conflict Detected

Query: {state.query[:100]}...

Found {len(state.conflicts)} conflicting pieces of evidence.
Consistency score: {state.consistency_score:.2f}

Response refused due to conflicting information."""

        elif state.notification_type == "uncertainty":
            return f"""⚠️ Low Confidence Response

Query: {state.query[:100]}...

Response generated with confidence score: {state.confidence_score:.2f}
Please review the response carefully."""

        elif state.notification_type == "refusal":
            return f"""❌ Query Refused

Query: {state.query[:100]}...

Reason: {state.refusal_reason or 'Insufficient evidence'}

Unable to provide reliable answer."""

        else:
            return f"""ℹ️ System Notification

Query: {state.query[:100]}...

{state.notification_message or 'Notification triggered'}"""