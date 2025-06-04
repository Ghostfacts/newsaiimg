"""Getting billing info on project"""

import datetime
import os

import boto3

client = boto3.client("ce")
# Dynamically set which project to report on (tag value)
PROJECT_TAG = os.environ.get("PROJECT_TAG", "unknonw")


def lambda_handler(event, context):  # pylint: disable=W0613,R1710
    """Function to generate an billing report"""
    # Time range: past 7 days
    end = datetime.date.today()
    start = end - datetime.timedelta(days=7)

    print(f"Fetching costs for project tag '{PROJECT_TAG}' from {start} to {end}")

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start.strftime("%Y-%m-%d"),
            "End": end.strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[
            {"Type": "TAG", "Key": "Project"},
            {"Type": "DIMENSION", "Key": "SERVICE"},
        ],
    )

    total = 0.0
    service_costs = {}

    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            # Remove the AWS prefix formatting from the tag
            project_value = group["Keys"][0].replace("Project$", "")
            service = group["Keys"][1]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])

            if project_value == PROJECT_TAG:
                service_costs[service] = service_costs.get(service, 0) + amount
                total += amount

    if not service_costs:
        return {
            "statusCode": 200,
            "body": f"No costs found for project '{PROJECT_TAG}' between {start} and {end}.",
        }

    report = [
        f"🧾 AWS Weekly Cost Report for Project: `{PROJECT_TAG}`",
        f"📅 Range: {start} → {end}",
        f"💰 Total: ${total:.2f}",
        "🔍 Service Breakdown:",
    ]

    for service, cost in sorted(service_costs.items(), key=lambda x: -x[1]):
        report.append(f"- ${cost:.2f} on {service}")

    final_report = "\n".join(report)
    print(final_report)

    return {"statusCode": 200, "body": final_report}
