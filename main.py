import praw
import os
from dotenv import load_dotenv
import openai
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

# Reddit API credentials
client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
username = os.getenv("REDDIT_USERNAME")
password = os.getenv("REDDIT_PASSWORD")
user_agent = os.getenv("USER_AGENT")

# OpenAI API key (optional)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Reddit instance
print("client_id =", client_id)
print("client_secret =", client_secret)
print("username =", username)
print("password =", password)
print("user_agent =", user_agent)

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    username=username,
    password=password,
    user_agent=user_agent,
)

# Function to extract Reddit username from profile URL
def extract_username(profile_url: str) -> str:
    if profile_url.endswith("/"):
        profile_url = profile_url[:-1]
    return profile_url.split("/")[-1]

# Function to fetch user data
def fetch_user_activity(reddit_username, limit=100):
    user = reddit.redditor(reddit_username)
    posts, comments = [], []

    try:
        print(f"Fetching data for u/{reddit_username}...")
        for post in tqdm(user.submissions.new(limit=limit), desc="Posts"):
            posts.append({
                "title": post.title,
                "body": post.selftext,
                "subreddit": str(post.subreddit),
                "url": f"https://www.reddit.com{post.permalink}"
            })
        for comment in tqdm(user.comments.new(limit=limit), desc="Comments"):
            comments.append({
                "body": comment.body,
                "subreddit": str(comment.subreddit),
                "url": f"https://www.reddit.com{comment.permalink}"
            })
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    return posts, comments

# Function to generate persona using OpenAI
def generate_persona(posts, comments):
    combined_text = ""
    for p in posts:
        combined_text += f"[Post in r/{p['subreddit']}]\n{p['title']}\n{p['body']}\n\n"
    for c in comments:
        combined_text += f"[Comment in r/{c['subreddit']}]\n{c['body']}\n\n"

    prompt = f"""
    Analyze the following Reddit user's posts and comments to create a detailed user persona.
    Include sections like:
    - Summary/Bio
    - Interests
    - Preferred Subreddits
    - Writing Style
    - Personality Traits
    - Opinions (political/social if any)
    - Any noticeable patterns

    Cite relevant text snippets with subreddit and URL where possible.

    TEXT:
    {combined_text[:8000]}  # limit to fit context
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful AI that builds user personas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating persona: {e}"

# Save persona to text file
def save_persona(username, persona_text):
    filename = f"persona_{username}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(persona_text)
    print(f"✅ Persona saved to {filename}")

# Main pipeline
def main():
    reddit_url = input("Enter Reddit profile URL (e.g. https://www.reddit.com/user/kojied): ").strip()
    target_username = extract_username(reddit_url)
    posts, comments = fetch_user_activity(target_username)
    
    if not posts and not comments:
        print("No data found for this user.")
        return
    
    persona = generate_persona(posts, comments)
    save_persona(target_username, persona)


if __name__ == "__main__":
    main()
