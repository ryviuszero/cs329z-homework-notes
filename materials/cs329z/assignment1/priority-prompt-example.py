# Reference snippet: email is the dictionary passed to run_priority.
# This only builds the prompt; it does not call the model or parse a reply.

classification_instructions = f"""Classify this email from the recipient's perspective at the time it was sent.

Choose exactly one category:
- urgent: The recipient needs to take action, make a decision, or handle an ongoing problem they are responsible for, and action is required today, on the next working day, or by a deadline within two working days. Working days are Monday through Friday, measured from the email's date.
- normal: Legitimate work or personal mail addressed to this recipient or a small working group, without a deadline within the next two working days.
- ignore: Advertising, newsletters, mass announcements, or automated notifications that require no action from this recipient.

Consider the sender, recipients, email date, subject, and body together. The subject alone does not determine priority. Advertising is not urgent just because it says "act now". An automated message requiring this recipient to act can be normal or urgent depending on its deadline. Personal messages from someone the recipient knows are normal.

Return only a JSON object with exactly two fields:
- "category": one of "urgent", "normal", or "ignore".
- "reason": one concise sentence explaining the classification using evidence from the email.

Email to classify:
<email>
From: {email["from"]}
To: {", ".join(email["to"])}
Date: {email["date"]}
Subject: {email["subject"]}
Body:
{email["body"]}
</email>
"""
