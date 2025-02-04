from reddit_scraping import scrape_posts_and_comments
from groq_llm_filtering import filter_using_llm
from tqdm import tqdm
import sys
import os
import pandas as pd

if len(sys.argv) > 1:
    # If an argument is provided, use it
    user_input = sys.argv[1]
else:
    # If no argument is provided, prompt the user
    user_input = input("Do you want to do LLM filtering process or not (y/n): ")


# Define list
subreddit_names = ["socialanxiety"]


for subreddit_name in tqdm(subreddit_names, desc="Reddit Scraping"):

    # If your process is incomplete.
    if f"{subreddit_name}_pure.csv" in os.listdir('../Data/'):
        df = pd.read_csv(f"{subreddit_name}_pure.csv")
        print("Data read directly")
    else:
        # Scraping from scratch
        df = scrape_posts_and_comments(subreddit_name=subreddit_name)
        df.to_csv(f"Data/{subreddit_name}_pure_en.csv", index=False)
        print(f"{subreddit_name} pure data was saved.")

    # If your request limit exceeded. Please select 'n'
    if user_input == "y":
        print("Rich guy :), Lets start filtering by using LLM")
        llm_filtered_df = filter_using_llm(df=df)
        llm_filtered_df.to_csv(f"Data/{subreddit_name}_llm_filtered_en.csv", index=False)
        print(f"{subreddit_name} filtered data was saved.")
    else:
        print("I hope you can do ASAP. I'm sorry :(")


