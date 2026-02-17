import re, emoji

class TextProcessor:
    def __init__(self):
        self.punctuation_pattern = r'[^\w\s]'
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.html_tags_pattern = re.compile(r'<.*?>')

    def clean(self, text:str) -> str:
        """
        Clean text for sentiment analysis
        
        Steps:
        1. Remove URLs and HTML tags
        2. Convert emojis to text (:face_with_tears_of_joy:)
        3. Lowercase
        4. Reduce excessive punctuation (!!!! → !)
        5. Reduce excessive letters (yesssss → yess)
        6. Normalize whitespace
        """
        try: 
            text = self.url_pattern.sub("", text)
            text = self.html_tags_pattern.sub("", text)

            text = emoji.demojize(text, delimiters=(" ", " "))
            text = text.lower().strip()

            text = re.sub(r'(\W)\1+', r'\1', text)  # reduce excessive punctuation
            text = re.sub(r'([a-zA-Z])\1{2,}', r'\1\1', text)   # reduce excessive letters
            
            text = ' '.join(text.split())
            
            words = text.split()
            if len(words) > 400:
                text = ' '.join(words[:400])
                
            return text.strip()
        
        except Exception:
            return ""

    @staticmethod
    def is_valid(text: str) -> bool:
        """
        Check if text is valid for analysis
        
        Invalid if:
        - less than 2 characters (after cleanup)
        - empty or none
        """
        if not text or not isinstance(text, str):
            return False
        
        text = text.strip()
        
        if not text:
            return False
        
        if len(text) < 2:
            return False
    
        return True


if __name__ == "__main__":
    preprocessor = TextProcessor()
    test_cases = [
        "Great video! 😍 https://link.com",
        "First!",
        "None",
        True,
        "Love it",
        "Prettyyyyy",
        "😍😍😍",
        "so cool??",
        "AMAZINGGG!!!!!",
    ]
    for test in test_cases:
        cleaned = preprocessor.clean(test)
        print(f"Original: {test}")
        print(f"Cleaned:  {cleaned}")
        print()

    valid_tests = [
        ("First!", True),
        ("Love it", True),
        ("ok", True),
        ("no", True),
        ("😍😍😍", True),
        ("", False), 
        ("   ", False),  
        ("a", False), 
        ("!", False),
        (" ", False),]
    
    for text, expected in valid_tests:
        cleaned = preprocessor.clean(text)
        result = preprocessor.is_valid(cleaned)
        try:
            assert result == expected
        except AssertionError:
            raise
    
    print("All validation tests passed! ✅")