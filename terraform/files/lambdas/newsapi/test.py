import genai

# Example usage
if __name__ == "__main__":
    bedrock = genai.Bedrock(region="eu-west-2")

    news_text = """
    The security council met on March 10th to discuss cybersecurity risks in cloud infrastructure.
    Attendees included Alice (CTO), Bob (Security Lead), and Charlie (Ops Manager).
    The team reviewed recent incidents and agreed to implement new IAM policies.
    Next steps include a follow-up meeting next month to assess progress.
    """

    results = bedrock.news_reviews(news_text)
    for result in results:
        print(result)