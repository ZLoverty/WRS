import feedparser
import datetime
import time
from google import genai
import yaml
import os

prompt = (
        "You are a helpful assistant that summarizes scientific articles. " +
        "Here are the latest articles from a feed source:" +
        "{}" + 
        "In a few sentences, answer the following questions:" +
        "What type of article is this?" +
        "What research area is this research about?" +
        "what is the most important message of this publication?" +
        "What applications does this research have?"
    )

prompt2 = (
        "You are a helpful assistant that summarizes scientific articles. " +
        "Here are many summaries of a collection of articles." +
        "{}" + 
        "In a few sentences and concise language, describe the major themes of these articles." + 
        "Provide links to a few important articles in [[number]](url)] style." +
        "The links should be integrated into the text, not listed separately."
)

model_name = 'gemini-2.0-flash'

try:
    # Attempt to get the API key from an environment variable
    # It's recommended to set your API key as an environment variable
    # for security reasons. Replace "YOUR_API_KEY" with your actual key
    # if you want to set it directly in the code (not recommended for production).
    # For example: genai.configure(api_key="YOUR_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        print("Warning: GOOGLE_API_KEY environment variable not set. Summarization will be skipped.")
    else:
        # Correctly initialize the client for the new SDK
        client = genai.Client(api_key=GOOGLE_API_KEY)
except ImportError:
    print("Warning: The 'google.genai' package is not installed. Summarization will be skipped.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}. Summarization will be skipped.")



def get_articles_from_rss(feed_url: str):
    """
    Parses an RSS feed and returns a list of article entries.

    Args:
        feed_url: The URL of the RSS feed.

    Returns:
        A list of feedparser entry objects.
    """
    try:
        # Parse the feed from the URL
        parsed_feed = feedparser.parse(feed_url)
        
        # Check for errors in parsing
        if parsed_feed.bozo:
            # Bozo bit is set to 1 if the feed is not well-formed
            error_message = parsed_feed.bozo_exception
            print(f"Warning: Feed at {feed_url} is not well-formed. Error: {error_message}")
        
        return parsed_feed.entries
        
    except Exception as e:
        print(f"An unexpected error occurred while fetching {feed_url}: {e}")
        return []

def filter_articles_by_date_range(articles: list, start_date: datetime.date, end_date: datetime.date) -> list:
    """
    Filters a list of articles to include only those published within a specific date range,
    and attempts to exclude non-research articles.
    This version checks for both 'published_parsed' and 'updated_parsed' for robustness.

    Args:
        articles: A list of feedparser entry objects.
        start_date: The start of the date range to filter by.
        end_date: The end of the date range to filter by.
        source_name: The name of the feed source.

    Returns:
        A list of filtered article dictionaries.
    """
    filtered_articles = []

    for entry in articles:
        # --- Keyword Filtering Logic ---
        is_research = True
        title_lower = entry.get("title", "").lower()
            
        # --- Date Filtering Logic ---
        date_struct = None
        # Feeds can use 'published_parsed' or 'updated_parsed'. We check for both.
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            date_struct = entry.published_parsed
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            date_struct = entry.updated_parsed

        # If we found a valid date structure, proceed with filtering.
        if date_struct:
            # Convert the 9-tuple time struct to a datetime object
            published_datetime = datetime.datetime.fromtimestamp(time.mktime(date_struct))
            
            # Compare just the date part to see if it's in the range
            if start_date <= published_datetime.date() <= end_date:
                filtered_articles.append({
                    'title': entry.get('title', 'No title'),
                    'url': entry.get('link', 'No link'),
                    'published_datetime': published_datetime,
                    'source': entry.get('source', 'Unknown source'),
                    'summary': entry.get('summary', 'No summary'),
                    'content': entry.get('content', []),
                    'keywords': entry.get('tags', []),
                })
    return filtered_articles

def summarize_article(article_entry) -> dict:
    """
    Summarizes the article content using a generative AI model.
    
    Args:
        article: The article entry to summarize.
    
    Returns:
        A summary of the article (dict).
    """

    # Generate content
    response = client.models.generate_content(
        model = model_name, 
        contents = prompt.format(article_entry)
    )
    
    return response.text

def analyze_article_collection(articles_summaries: list) -> str:
    """
    Analyzes a collection of articles and returns a summary for each.
    
    Args:
        articles: A list of article entries to analyze.
    
    Returns:
        A list of summaries for each article.
    """
    summaries = "\n\n\n".join(articles_summaries)
    
    response = client.models.generate_content(
        model = model_name, 
        contents = prompt2.format(summaries)
    )

    return response.text

def html_wrap(html_body: str, width: int) -> str:
    """
    Wraps the given HTML paragraph in given width.
    
    Args:
        text: The text to wrap.
    
    Returns:
        The wrapped text in HTML format.
    """

    final_html = f"""
    <html>
    <head></head>
    <body>
        <div style="max-width: {width:d}px; margin: 0 auto; font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6;">
        {html_body}
        </div>
    </body>
    </html>
    """

    return final_html

def read_rss_from_yaml(rss_dir: str) -> dict:
    """
    Reads the RSS data from the YAML file and returns it.
    """
    with open(rss_dir, "r") as file:
        rss_data = yaml.safe_load(file)
    rss_data_processed = {}
    if rss_data:
        for item in rss_data:
            rss_data_processed[item["name"]] = item["url"]
    return rss_data_processed

if __name__ == "__main__":
    # Define the RSS feeds you want to check
    # Found via searching for "Nature RSS feed" and "Science magazine RSS feed"
    target_feeds = {
        "Nature": "http://feeds.nature.com/nature/rss/current",
        "Science": "https://www.science.org/rss/news_current.xml"
    }

    all_new_articles = []
    
    # Get the date range for the last 7 days
    today = datetime.date.today()
    one_day_ago = today - datetime.timedelta(days=7)
    
    print(f"Fetching articles published between {one_day_ago.strftime('%Y-%m-%d')} and {today.strftime('%Y-%m-%d')}\n")

    for source_name, feed_url in target_feeds.items():
        print(f"--- Processing feed: {source_name} ---")
        
        # Get all entries from the current feed
        all_entries = get_articles_from_rss(feed_url)
        
        if all_entries:
            # Filter the entries for the last week, passing in the source name
            todays_articles = filter_articles_by_date_range(
                all_entries, one_day_ago, today, source_name
            )
            if todays_articles:
                all_new_articles.extend(todays_articles)
                print(f"Found {len(todays_articles)} new articles from this week.")
            else:
                print("No new articles found for this week.")
        
        print("-" * (len(source_name) + 20) + "\n")
            
    if all_new_articles:
        print(f"--- Found a total of {len(all_new_articles)} new articles from this week ---")
        
        # Sort all articles by publication time, newest first
        all_new_articles.sort(key=lambda x: x['published_datetime'], reverse=True)
        
        for i, article in enumerate(all_new_articles, 1):
            pub_date = article['published_datetime'].strftime('%Y-%m-%d')
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']} ({pub_date})")
            print(f"   URL: {article['url']}")
    else:
        print("No new articles found in Nature or Science from the past week.")
