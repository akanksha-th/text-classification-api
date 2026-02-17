from transformers import pipeline

print("Downloading sentiment model...")
sentiment = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)

print("Model downloaded successfully!")

print("\n=-="*20)
print("Testing with sample text...")
result1 = sentiment("This is amazing!")
print(result1)
print("=-="*20)
result2 = sentiment("What are you even saying? bs!!")
print(result2)
print("=-="*20)
result2 = sentiment("Meh")
print(result2)
print("=-="*20)