# Enabling the live AWS Bedrock path

Rescind's Bedrock integration is written and tested, but has never been executed
against live AWS: the credentials available in the build environment were
rejected by STS. This is the five-minute browser task that flips it from
"integrated" to "exercised", and it is all done from a phone.

**Never paste the keys into a chat.** They go straight from the AWS console into
GitHub's secret store.

---

## 1. Turn on Bedrock model access (2 min)

Bedrock models are off by default and access is per-region.

1. AWS console → search **Bedrock** → open it.
2. **Set the region first**, top right. Use **US East (N. Virginia) / us-east-1**
   — it has the widest model availability. Whatever you pick must match step 3.
3. Left menu → **Model access** (*Acceso a modelos*) → **Modify model access**
   (*Modificar acceso a modelos*).
4. Tick:
   - **Amazon → Titan Text Embeddings V2**
   - **Anthropic → Claude Sonnet** (any current Sonnet)
5. **Submit** (*Enviar*). Titan is usually instant. Anthropic may ask for a short
   use-case description — write something plain and true, for example:
   *"Hackathon project: an agent that advises on product-recall decisions in food
   distribution. Claude returns a release/hold recommendation from supplied
   records."*

Wait until both show **Access granted** (*Acceso concedido*).

## 2. Create a least-privilege IAM user (2 min)

Rescind's own database role holds no DELETE and no DDL. The AWS credential
should be equally narrow — do **not** attach `AmazonBedrockFullAccess`.

1. Console → **IAM** → **Policies** → **Create policy** → **JSON** tab.
2. Paste this, then save it as **`RescindBedrockInvoke`**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeOnlyTheTwoModelsRescindUses",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:*:*:inference-profile/*"
      ]
    }
  ]
}
```

That grants invoke on exactly the two models Rescind calls and nothing else: no
model management, no account access, no other service. The `inference-profile`
line is needed because `rescind/config.py` calls Claude through a cross-region
inference profile (`us.anthropic.…`), not the bare foundation-model ARN.

3. **IAM → Users → Create user**, name it **`rescind-ci`**. Do **not** give it
   console access.
4. **Attach policies directly** → tick **`RescindBedrockInvoke`** → create.
5. Open the user → **Security credentials** → **Create access key** → choose
   **Application running outside AWS** → create.
6. Leave that page open; you need both values once, in the next step.

## 3. Put the keys in GitHub (1 min)

1. Go to **github.com/phazon2/rescind → Settings → Secrets and variables →
   Actions → New repository secret**.
2. Add three secrets, exactly these names:

| Name | Value |
|---|---|
| `AWS_ACCESS_KEY_ID` | the access key ID from step 2 |
| `AWS_SECRET_ACCESS_KEY` | the secret access key from step 2 |
| `AWS_REGION` | `us-east-1` (or whichever region you enabled in step 1) |

3. Close the AWS page. You will not need the secret value again — if it is ever
   lost, delete the key and make a new one.

## 4. Run it (30 s)

**Actions → verify-live-aws → Run workflow.**

It is dormant while the secrets are missing, so it has been passing by exiting
early. With the secrets present it starts a CockroachDB cluster, applies the
schema, and runs `scripts/probe_bedrock.py`, which certifies the one thing the
offline suite cannot:

- Titan really returns the **1024 dimensions** the schema hardcodes as
  `VECTOR(1024)`;
- a real Titan vector round-trips through `VECTOR(1024)` with ~0 self-distance;
- Claude returns a verdict the strict parser accepts.

It commits `ci/bedrock.json` as evidence. Once that file exists and is green,
the README's "AWS Bedrock was never called" caveat comes out and the demo page
stops describing its embeddings as stand-ins.

## Cost

Effectively nothing. The probe makes one embedding call and one short Claude
call — well under a cent. Bedrock has no standing charge; you pay per token.

## If something goes wrong

| Symptom | Cause |
|---|---|
| `AccessDeniedException` on Titan | Model access not granted in **that** region — recheck step 1 with the region selector matching `AWS_REGION` |
| `AccessDeniedException` on Claude | Anthropic access still pending approval, or the `inference-profile` line was dropped from the policy |
| `ValidationException` about model id | The Claude model in `rescind/config.py` is not available in your region; pick one that is and change that line |
| `InvalidClientTokenId` | The access key was mistyped into the secret, or the key was deleted |
| Workflow says "This job is dormant" | A secret name is misspelled — they are case-sensitive |
