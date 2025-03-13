# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# snippet-start:[bedrock-runtime.example_code.hello_bedrock_invoke.complete]

"""
Uses the Amazon Bedrock runtime client InvokeModel operation to send a prompt to a model.
"""
import logging
import json
import boto3


from botocore.exceptions import ClientError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def invoke_model(brt, model_id, prompt):
    """
    Invokes the specified model with the supplied prompt.
    param brt: A bedrock runtime boto3 client
    param model_id: The model ID for the model that you want to use.
    param prompt: The prompt that you want to send to the model.

    :return: The text response from the model.
    """

    # Format the request payload using the model's native structure.
    native_request = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0.5,
            "topP": 0.9
        }
    }

    # Convert the native request to JSON.
    request = json.dumps(native_request)

    try:
        # Invoke the model with the request.
        response = brt.invoke_model(modelId=model_id, body=request)

        # Decode the response body.
        model_response = json.loads(response["body"].read())

        # Extract and print the response text.
        response_text = model_response["results"][0]["outputText"]
        return response_text

    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        raise


def main():
    """Entry point for the example. Uses the AWS SDK for Python (Boto3)
    to create an Amazon Bedrock runtime client. Then sends a prompt to a model
    in the region set in the callers profile and credentials.
    """

    # Create an Amazon Bedrock Runtime client.
    brt = boto3.client(
        "bedrock-runtime",
        "eu-west-2"
    )

    # Set the model ID, e.g., Amazon Titan Text G1 - Express.
    model_id = "amazon.titan-text-express-v1"


    transcript_example_text=f'''
    James: Hi Sarah, shall we go over the status of the Maxwell account marketing project?
    Sarah: Sure, that sounds good. What's on your agenda for today?
    James: I wanted to touch base on the timeline we discussed last week and see if we're
    still on track to hit those deadlines. How did the focus group go earlier this week?
    Sarah: The focus group went pretty well overall. We got some good feedback on the new
    branding concepts that I think will help refine our ideas. The one hiccup is that the
    product samples we were hoping to show arrived late, so we weren't able to do the
    unboxing and product trial portion that we had planned.
    James: Okay, good to hear it was mostly positive. Sorry to hear about the product
    sample delay. Did that impact our ability to get feedback on the premium packaging
    designs?
    Sarah: It did a little bit - we weren't able to get as detailed feedback on unboxing
    experience and the tactile elements we were hoping for. But we did get high-level
    input at least. I'm hoping to schedule a follow up focus group in two weeks when the
    samples arrive.
    James: Sounds good. Please keep me posted on when that follow up will happen. On the
    plus side, it's good we built in a buffer for delays like this. As long as we can get
    the second round of feedback by mid-month, I think we can stay on track.Sarah: Yes,
    I'll make sure to get that second session booked and keep you in the loop.
    How are things looking for the website development and SEO optimization? Still on pace
    for the planned launch?
    James: We're in good shape there. The initial site map and wireframes are complete and
    we began development work this week. I'm feeling confident we can hit our launch goal
    of March 15th if all goes smoothly from here on out. One request though - can you send
    me any new branding assets or guidelines as soon as possible? That will help ensure it
    gets incorporated properly into the site design.
    Sarah: Sure, will do. I should have those new brand guidelines over to you by early
    next week once we finalize with Maxwell.
    James: Sounds perfect, thanks! Let's plan to meet again next Thursday and review the
    focus group results and new launch timeline in more detail.
    Sarah: Works for me! I'll get those calendar invites out.
    James: Great, talk to you then.
    Sarah: Thanks James, bye!
    '''


    prompt=f'''
    Human: I am going to give you transcript of a meeting extract key informations,
    members of meeting and minutes of the meeting,key takeaways and next step .
    Here is the transcript:<transcript>{transcript_example_text}</transcript>
    Assistant:'''

    # Send the prompt to the model.
    response = invoke_model(brt, model_id, prompt)

    print(f"Response: {response}")

    logger.info("Done.")


if __name__ == "__main__":
    main()

 # snippet-end:[bedrock-runtime.example_code.hello_bedrock_invoke.complete]