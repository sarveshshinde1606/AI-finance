import google.generativeai as genai

API_KEY = "YAHAN_APNI_REAL_AI_STUDIO_KEY_DALO"

try:
    print("Configuring API...")
    genai.configure(api_key=API_KEY)

    print("Creating model...")
    model = genai.GenerativeModel("gemini-1.5-flash")

    print("Generating content...")
    response = model.generate_content(
        "Say hello in one short sentence."
    )

    print("Response object received.")
    print("RAW RESPONSE:", response)

    print("TEXT OUTPUT:")
    print(response.text)

except Exception as e:
    print("ERROR OCCURRED:")
    print(e)