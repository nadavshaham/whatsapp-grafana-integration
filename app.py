#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("whatsapp-mgr")

# WhatsApp API configuration
WHIN_API_URL = "https://whin2.p.rapidapi.com/send2group"
WHIN_API_HEADERS = {
    'Content-Type': 'application/json',
    'x-rapidapi-host': 'whin2.p.rapidapi.com',
    'x-rapidapi-key': os.environ.get('WHIN_API_KEY', '')
}


def format_grafana_alert(alert_data):
    """
    Format Grafana alert data into a readable WhatsApp message

    Args:
        alert_data: Dictionary containing Grafana alert data

    Returns:
        str: Formatted message for WhatsApp
    """
    try:
        # Extract status
        status = alert_data.get('status', 'unknown').upper()

        # Extract alert information
        message_parts = []

        # Add header with status
        message_parts.append(f"🚨 *ALERT {status}* 🚨")

        # Loop through each alert in the alerts array
        for alert in alert_data.get('alerts', []):
            alert_name = alert.get('labels', {}).get('alertname', 'Unknown Alert')
            message_parts.append(f"\n*Alert*: {alert_name}")

            namespace = alert.get('labels', {}).get('namespace', 'N/A')
            pod = alert.get('labels', {}).get('pod', 'N/A')
            message_parts.append(f"*Resource*: {namespace}/{pod}")

            # Get summary from annotations
            summary = alert.get('annotations', {}).get('summary', 'No details available')
            message_parts.append(f"*Summary*: {summary}")

            # Format start time if available
            starts_at = alert.get('startsAt')
            if starts_at:
                try:
                    # Parse ISO format and convert to more readable format
                    start_time = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                    message_parts.append(f"*Started*: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except (ValueError, TypeError):
                    message_parts.append(f"*Started*: {starts_at}")

            # Add link to Grafana
            generator_url = alert.get('generatorURL', '')
            if generator_url:
                message_parts.append(f"*Link*: {generator_url}")

        # Add external URL if available
        external_url = alert_data.get('externalURL', '')
        if external_url:
            message_parts.append(f"\n*Grafana*: {external_url}")

        return "\n".join(message_parts)
    except Exception as e:
        logger.error(f"Error formatting alert message: {e}")
        return f"Alert {alert_data.get('status', 'unknown').upper()}: Error processing alert details. Please check Grafana."


def send_to_whatsapp(message):
    """
    Send a message to WhatsApp via the Whin API

    Args:
        message: Message text to send

    Returns:
        dict: Response from the API
    """
    try:
        payload = {"text": message}

        # Log the message being sent (excluding sensitive data)
        logger.info(f"Sending message to WhatsApp (length: {len(message)})")

        # Check if API key is set
        if not WHIN_API_HEADERS.get('x-rapidapi-key'):
            logger.error("WHIN_API_KEY environment variable is not set")
            return {"status": "error", "message": "API key not configured"}

        response = requests.post(
            WHIN_API_URL,
            headers=WHIN_API_HEADERS,
            json=payload
        )

        # Log response code
        logger.info(f"WhatsApp API response status: {response.status_code}")

        if response.status_code == 200:
            return {"status": "success", "message": "Message sent to WhatsApp"}
        else:
            logger.error(f"WhatsApp API error: {response.text}")
            return {"status": "error", "message": f"API error: {response.status_code}", "details": response.text}

    except Exception as e:
        logger.error(f"Error sending to WhatsApp: {e}")
        return {"status": "error", "message": f"Error: {str(e)}"}


def process_message(message_json):
    """
    Process the input message JSON

    Args:
        message_json: JSON string or dict containing the message data

    Returns:
        dict: Result of processing
    """
    try:
        # If the input is a string, parse it as JSON
        if isinstance(message_json, str):
            message_data = json.loads(message_json)
        else:
            message_data = message_json

        logger.info(f"Processing message data of type: {type(message_data)}")

        # Check if this looks like a Grafana alert
        if isinstance(message_data, dict) and ('alerts' in message_data or 'status' in message_data):
            logger.info("Detected Grafana alert format")

            # Format the alert message for WhatsApp
            formatted_message = format_grafana_alert(message_data)

            # Send the formatted message to WhatsApp
            whatsapp_result = send_to_whatsapp(formatted_message)

            # Return combined result
            return {
                "status": whatsapp_result.get("status", "unknown"),
                "message": whatsapp_result.get("message", ""),
                "formatted_alert": formatted_message
            }
        else:
            # Just print the message for non-Grafana alert format
            logger.info(f"Regular message (not Grafana alert): {json.dumps(message_data, indent=2)}")
            print(f"Message content: {json.dumps(message_data, indent=2)}")

            return {
                "status": "success",
                "message": "Message processed successfully (not an alert)",
                "data": message_data
            }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return {"status": "error", "message": f"Invalid JSON format: {e}"}
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"status": "error", "message": f"Error processing message: {e}"}


def main():
    """
    Main function that handles input from different sources:
    1. Command line argument
    2. Environment variable
    3. Stdin
    """
    parser = argparse.ArgumentParser(description='WhatsApp message processor')
    parser.add_argument('--message', '-m', type=str, help='JSON message to process')
    args = parser.parse_args()

    # First check command line argument
    if args.message:
        logger.info("Reading message from command line argument")
        result = process_message(args.message)

    # Then check environment variable
    elif 'MESSAGE_JSON' in os.environ:
        logger.info("Reading message from MESSAGE_JSON environment variable")
        result = process_message(os.environ['MESSAGE_JSON'])

    # Finally check stdin
    elif not sys.stdin.isatty():
        logger.info("Reading message from standard input")
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            result = process_message(stdin_data)
        else:
            result = {"status": "error", "message": "Empty input from stdin"}

    # No input provided
    else:
        logger.error("No message input provided. Use --message argument, MESSAGE_JSON environment variable, or pipe data via stdin")
        result = {"status": "error", "message": "No input provided"}
        sys.exit(1)

    # Output the result as JSON
    print(json.dumps(result, indent=2))

    # Exit with error code if processing failed
    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    logger.info("Starting WhatsApp Manager")
    main()
