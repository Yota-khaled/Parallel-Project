import requests
import threading
import instaloader
import tkinter as tk
from tkinter import ttk, messagebox
from playwright.sync_api import sync_playwright
from PIL import Image, ImageTk
from io import BytesIO
import time

# A global dictionary to store results from various threads safely
results = {}
results_lock = threading.Lock()  # Ensures thread-safe access to shared data


# Class for handling Facebook data scraping using Playwright
class FacebookFetcher:
    def __init__(self):
        """Initializes the Playwright browser for Facebook scraping."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

    def get_basic_info(self, user_id):
        """
        Fetch basic profile information from a Facebook user profile page.
        Args:
            user_id (str): The URL or ID of the Facebook user profile.
        Returns:
            dict: A dictionary containing profile information such as Name, Profile Picture, etc.
        """
        context = self.browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the Facebook profile URL
            page.goto(f"{user_id}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000)  # Additional time for page load an 5 seconds 

            profile_info = {"ID": user_id}

            # Username
            try:
                name_element = page.query_selector("h1")
                profile_info["Name"] = name_element.inner_text() if name_element else "N/A"
            except Exception:
                profile_info["Name"] = "N/A"

            # Profile picture using the new CSS Selector
            try:
                profile_picture_element = page.query_selector(
                    "div.x15sbx0n:nth-child(1) > div:nth-child(1) > a:nth-child(1) > div:nth-child(1) > svg:nth-child(1) > g:nth-child(2) > image:nth-child(1)"
                )
                profile_info["Profile Picture"] = profile_picture_element.get_attribute(
                    "xlink:href"
                ) if profile_picture_element else "N/A"
            except Exception:
                profile_info["Profile Picture"] = "N/A"

            return profile_info
        except Exception as e:
            return {"error": str(e)}  # Capture errors and return them for debugging
        finally:
            context.close()

    def close(self):
        """Closes the browser and stops Playwright."""
        self.browser.close()
        self.playwright.stop()


# Class for handling Twitter data scraping using Playwright
class TwitterFetcher:
    def __init__(self):
        """Initializes the Playwright browser for Twitter scraping."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True) # Headless browser

    def get_tweets(self, username, count=5):
        """
        Fetch the latest tweets and profile details from a Twitter user profile.
        Args:
            username (str): The username of the Twitter account (e.g., 'jack').
            count (int): The number of tweets to retrieve. Default is 5.
        Returns:
            list: A list of dictionaries containing tweets and profile details.
        """
        context = self.browser.new_context()
        page = context.new_page()

        try:
            # Navigate to the Twitter profile page
            page.goto(f"https://twitter.com/{username}")

            # Wait for tweets to load
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(5000) # Extra time for full content to load

             # Initialize the list to store tweets
            tweets = []
            # Select profile picture using a valid selector
            profile_picture_element = page.query_selector("img[src*='profile_images']")
            profile_picture_url = profile_picture_element.get_attribute("src") if profile_picture_element else "N/A"
            
            # Get the username display name
            user_name_element = page.query_selector("div[data-testid='UserName'] span")
            user_name = user_name_element.inner_text() if user_name_element else "N/A"

            # Get tweets
            tweet_elements = page.query_selector_all("article div[lang]")
            created_at_elements = page.query_selector_all("article time")
            image_elements = page.query_selector_all("article img[src]")
            
            # Extract tweets and associated data

            for i, tweet_element in enumerate(tweet_elements[:count]):
                text = tweet_element.inner_text()
                # Extract images (if available)
                image_url = image_elements[i].get_attribute("src") if i < len(image_elements) else "N/A"
                # Extract tweet creation time
                created_at = created_at_elements[i].get_attribute("datetime") if i < len(created_at_elements) else "N/A"
                
                # Append the tweet data to the list
                tweets.append({
                    "user_name": user_name,
                    "text": text,
                    "image": image_url,
                    "created_at": created_at,
                    "profile_picture": profile_picture_url
                })

            return tweets
        except Exception as e:
            return [{"error": f"Failed to fetch data: {e}"}]
        finally:
             # Clean up the context and browser            
            context.close()

    def close(self):
        """Closes the browser and stops Playwright."""
        self.browser.close()
        self.playwright.stop()


# Class to fetch Instagram profile information
class InstagramFetcher:
    def __init__(self):
        # Initialize Instaloader for Instagram data fetching
        self.loader = instaloader.Instaloader()

    def get_basic_info(self, username):
        """
        Fetch basic profile information from Instagram.

        Args:
            username (str): Instagram username.

        Returns:
            dict: Profile information including bio, follower count, and profile picture URL.
        """
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            return {
                "Username": profile.username,
                "Full Name": profile.full_name,
                "Bio": profile.biography,
                "Followers Count": profile.followers,
                "Following Count": profile.followees,
                "Posts Count": profile.mediacount,
                "Profile Picture": profile.profile_pic_url,
            }
        except Exception as e:
            return {"error": str(e)}

def display_twitter_profile_image(profile_picture_url, image_label):
    if profile_picture_url and profile_picture_url != "N/A":
        try:
            # Download the image from the URL
            img_data = requests.get(profile_picture_url).content
            img = Image.open(BytesIO(img_data))
            img = img.resize((100, 100))  # Resize to fit the interface
            img_tk = ImageTk.PhotoImage(img)

            # Update image_label to display the image
            image_label.config(image=img_tk)
            image_label.image = img_tk  # Keep the reference to avoid garbage collection
        except Exception as e:
            image_label.config(text=f"Error loading image: {e}")
            image_label.image = None
    else:
        image_label.config(text="No image available")


def display_facebook_profile_image(profile_picture_url, image_label):
    if profile_picture_url and profile_picture_url != "N/A":
        try:
            # Download the image from the URL
            img_data = requests.get(profile_picture_url).content
            img = Image.open(BytesIO(img_data))
            img = img.resize((100, 100))  # Resize to fit the interface
            img_tk = ImageTk.PhotoImage(img)

            # Update image_label to display the image
            image_label.config(image=img_tk)
            image_label.image = img_tk  # Keep the reference to avoid garbage collection
        except Exception as e:
            image_label.config(text=f"Error loading image: {e}")
            image_label.image = None
    else:
        image_label.config(text="No image available")


def display_instagram_profile_image(profile_picture_url, image_label):
    if profile_picture_url and profile_picture_url != "N/A":
        try:
            # Download the image from the URL
            img_data = requests.get(profile_picture_url).content
            img = Image.open(BytesIO(img_data))
            img = img.resize((100, 100))  # Resize to fit the interface
            img_tk = ImageTk.PhotoImage(img)

            # Update image_label to display the image
            image_label.config(image=img_tk)
            image_label.image = img_tk  # Keep the reference to avoid garbage collection
        except Exception as e:
            image_label.config(text=f"Error loading image: {e}")
            image_label.image = None
    else:
        image_label.config(text="No image available")


# Main function to fetch data from selected platforms

def fetch_data_from_platform(platform_name, user_input, result_label, image_label):
    start_time = time.time()  # Capture the start time
    global results
    elapsed_time = 0
    """
    Fetch data from a specified platform (Facebook, Twitter, or Instagram).

    Args:
        platform_name (str): The platform name (e.g., 'Facebook').
        user_input (dict): User inputs containing usernames or IDs.
        result_label (tk.Label): Label to display the results.
        image_label (tk.Label): Label to display the profile image.
    """
    try:
        if platform_name == "Facebook":
            fetcher = FacebookFetcher()
            user_id = user_input.get("facebook_user_id", "")
            data = fetcher.get_basic_info(user_id)
            fetcher.close()
            # When retrieving Facebook data, show the profile picture
            profile_picture_url = data.get("Profile Picture", "N/A")
            display_facebook_profile_image(profile_picture_url, image_label)



        elif platform_name == "Twitter":
            fetcher = TwitterFetcher()
            username = user_input.get("twitter_username", "")
            data = fetcher.get_tweets(username)
            fetcher.close()
            # When retrieving Twitter data, pass the profile picture URL to the function
            if data and isinstance(data, list):
                profile_picture_url = data[0].get("profile_picture", "N/A")  # Retrieve the profile picture URL
                display_twitter_profile_image(profile_picture_url, image_label)  # Display the image
            else:
                data = {"error": "Unknown Platform"}
                
                
        elif platform_name == "Instagram":
            fetcher = InstagramFetcher()
            username = user_input.get("instagram_username", "")
            data = fetcher.get_basic_info(username)
            profile_picture_url = data.get("Profile Picture", "N/A")

            display_instagram_profile_image(profile_picture_url, image_label)



        else:
            data = {"error": "Unknown Platform"}
            
        end_time = time.time()  # Capture the end time
        elapsed_time = round(end_time - start_time, 2)  # Calculate elapsed time
        # Format the result text with the performance time
        if platform_name == "Twitter" and isinstance(data, list):
            for tweet in data:
                tweet["Performance"] = f"Time Taken: {elapsed_time} seconds"
            result_text = "\n\n".join(
                [f"Tweet {i + 1}:\n" + "\n".join([f"{k}: {v}" for k, v in tweet.items()]) for i, tweet in
                 enumerate(data)]
            )
        else:
            data["Performance"] = f"Time Taken: {elapsed_time} seconds"
            result_text = "\n".join([f"{k}: {v}" for k, v in data.items()])

            # Handle displaying the profile image
            image_url = data.get("Profile Picture") or None
            if image_url:
                try:
                    # Download the image using requests
                    img_data = requests.get(image_url).content
                    img = Image.open(BytesIO(img_data))
                    img = img.resize((100, 100))  # Resize to fit the interface
                    img_tk = ImageTk.PhotoImage(img)

                    # Update image_label to display the image
                    image_label.config(image=img_tk)
                    image_label.image = img_tk  # Keep the reference to avoid garbage collection
                except Exception as e:
                    image_label.config(text=f"Error loading image: {e}")
                    image_label.image = None
            else:
                image_label.config(text="No image available")

        # Update the result interface with the retrieved data
        with results_lock:
            results[platform_name] = data
        result_label.config(text=result_text)

    except Exception as e:
        with results_lock:
            results[platform_name] = {"error": str(e)}
        result_label.config(text=f"Error fetching data: {e}")
        print(f"Error fetching {platform_name} data: {e}")


# Open a window for each thread with input fields and results display
def open_thread_windows():
    try:
         # Get the number of threads from the user input
        num_threads = int(thread_count_entry.get())
    except ValueError:
        # Show error message if input is not a valid number
        messagebox.showerror("Invalid Input", "Please enter a valid number")
        return
    
    # Function to create a new window for each thread
    def create_fetch_window(thread_index):
        # Create a new top-level window for the thread
        window = tk.Toplevel(root)
        window.title(f"Thread {thread_index + 1}")
        window.geometry("400x400")

         # Create a frame for scrollable content
        frame = tk.Frame(window)
        frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        # Configure the canvas to update its scroll region when the frame size changes
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Attach the frame to the canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar into the frame
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

         # Add a label to identify the thread
        tk.Label(scrollable_frame, text=f"Thread {thread_index + 1}", font=("Arial", 16, "bold")).pack(pady=10)

        # Add a dropdown for selecting the platform
        tk.Label(scrollable_frame, text="Select Platform:", font=("Arial", 12)).pack(pady=5)
        platform_var = ttk.Combobox(scrollable_frame, values=["Facebook", "Instagram", "Twitter"], state="readonly",
                                    font=("Arial", 10))
        platform_var.pack(pady=5)
        platform_var.set("Facebook")# Set default value
        
        # Add an entry field for username/ID input
        tk.Label(scrollable_frame, text="Enter Username/ID:", font=("Arial", 12)).pack(pady=5)
        username_entry = tk.Entry(scrollable_frame, font=("Arial", 10))
        username_entry.pack(pady=5)
        
        # Label to display results
        result_label = tk.Label(scrollable_frame, text="Results will appear here", wraplength=350, justify="left",font=("Arial", 10))
        result_label.pack(pady=10)
        
        # Label to display profile image placeholder
        image_label = tk.Label(scrollable_frame, text="Profile image will appear here", wraplength=350, justify="left", font=("Arial", 10))
        image_label.pack(pady=10)
        
        # Import Thread module for running fetch operations in a separate thread
        from threading import Thread

        fetch_button = tk.Button(
            scrollable_frame, text="Fetch Data", font=("Arial", 10, "bold"),
            command=lambda: Thread(target=fetch_data_from_platform,
                                   args=(platform_var.get(),# Selected platform
                                         
                                         {"facebook_user_id": username_entry.get(),
                                          "instagram_username": username_entry.get(),
                                          "twitter_username": username_entry.get()},

                                         result_label, image_label))
            .start()# Start the thread
        )

        fetch_button.pack(pady=10)

    for i in range(num_threads):
        create_fetch_window(i)
        
        
# Main window to input number of threads


root = tk.Tk()
root.title("Social Media Fetcher")
root.geometry("400x300")

# Add a label and entry field for the number of threads
tk.Label(root, text="Enter Number of Threads:", font=("Arial", 12)).pack(pady=10)
thread_count_entry = tk.Entry(root, font=("Arial", 12))
thread_count_entry.pack(pady=5)

# Button to open new windows for multiple threads
open_windows_button = tk.Button(root, text="Open Threads", font=("Arial", 12, "bold"), command=open_thread_windows)
open_windows_button.pack(pady=20)

root.mainloop()