# Short competition walkthrough

Use the local public demonstration until Google OAuth and Gemini live checks pass.
The demonstration is reconstructed and visibly labeled; do not describe it as a live
model result.

## Two-minute flow

1. Open `http://127.0.0.1:5173` and point out the signed-out state. Say: “The public
   example works without an account. Live model work and private saves require sign-in.”
2. Select **Open demonstration**. Point to **Demonstration — not a live verification**.
3. Read the claim: “More fluorescent puncta indicate increased autophagic activity.”
   Show the separate reported observation and interpretation. Say: “More spots are an
   observation; increased flux is an interpretation that needs more evidence.”
4. Show the `abstract access` and `product document access` labels. Explain that a paper
   identifier or HTTP response does not prove full-text access.
5. Open the exact evidence passages and limitations. Say: “The app checks source identity,
   quotation and location. A researcher still decides whether the passage really supports
   the claim.”
6. Show the qualified wording and next verification question. Enter a researcher edit,
   add a note, and select **Save edited wording**.
7. Export JSON. Explain that the export keeps the input, access levels, passages,
   limitations, decision and provenance.
8. End with: “The local demo is verified. Live Google sign-in and Gemini assessment are
   still blocked until their manual Free Tier setup and browser checks pass.”

## Evidence to show judges

- Actual desktop screenshot:
  [`react-demo-desktop.png`](../artifacts/competition-demo/react-demo-desktop.png)
- Actual canonical demonstration export:
  [`autophagy-demo-export.json`](../artifacts/competition-demo/autophagy-demo-export.json)
- Fresh public-source snapshot, kept separate from the demo:
  [`autophagy-case-record.json`](../artifacts/competition-demo/autophagy-case-record.json)
- Verification results and denominators:
  [`EVALUATION_PHASE_H.md`](EVALUATION_PHASE_H.md)

Do not claim measured accuracy, time savings, a live Gemini result, completed Google
OAuth, full-text access to PMC4502790, or public deployment.
