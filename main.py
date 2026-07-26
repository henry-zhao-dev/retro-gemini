import gemini_client

response = gemini_client.generate(
    prompt="Explain Git in one short paragraph.",
    model="gemini-2.5-flash",
)

print(response)
