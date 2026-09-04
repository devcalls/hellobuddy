
# HelloBuddy Setup Instructions 🚀

Step by step guide to setup HelloBuddy CLI tool.

---

# 🔑 Credentials Setup Guide

Follow these steps to create your free accounts, get your API tokens, and configure your `job_config.ini` file.

---

## 🔍 Part 1: Setting up Job Provider API Keys (For Job Scraping)

### Step 1: SerpAPI - Create an Account
1. Go to the [SerpApi Signup Page](https://serpapi.com/users/sign_up).
2. Register instantly using your **Google** or **GitHub** account, or sign up manually with your email.

### Step 2: SerpAPI - Get Your API Key
1. Once logged in, you will be taken directly to your **Dashboard**.
2. Look at the top center of the dashboard for your **Private API Key**. 
3. Click the **Copy** button. 
4. Keep this in a safe place, this value is later required in job_config.ini.

### Step 3: Adzuna - Create an Account
1. Go to the [Adzuna Developer Signup Page](https://developer.adzuna.com/).
2. Register instantly using your **Google** or sign up manually with your email.

### Step 4: Adzuna - Get Your API Key
1. Once logged in, generate API Key and a app Id.
4. Keep this in a safe place, this value is later required in job_config.ini.

### Step 5: Reed - Create an Account
1. Go to the [Reed Developer Signup Page](https://www.reed.co.uk/developers/Jobseeker).
2. Register instantly using your with your email.

### Step 6: Reed - Get Your API Key
1. Once logged in, generate API Key.
4. Keep this in a safe place, this value is later required in job_config.ini.


# 📧 Mailtrap Account Setup

Follow these steps to create your free Mailtrap account and capture your API keys.

---

## 🛠️ Step 1: Create Your Account
1. Navigate to the official [Mailtrap Sign Up Page](https://mailtrap.io/register/signup?ref=header).
2. Choose your preferred registration pathway:
   * **Social Sign-On:** Authenticate instantly using your **Google**, **GitHub**, or **Office 365** credentials.
   * **Traditional Email:** Supply your email address and create a strong, secure password.
3. If prompted via a verification banner, check your registration inbox and confirm your email link to unlock your full dashboard dashboard workspace.

---

## 🔑 Step 2: Extract Your API Key
Mailtrap defaults new accounts into an **Email Sandbox environment**—this allows your background Python daemon to safely test HTML email layouts without accidentally sending broken formatting to a live public inbox.

1. Locate the navigation tree in the left sidebar menu.
2. Click on **Sandboxes** header.
3. Click on **"My Sandbox"**.
4. Select the **API Tokens** menu option.
5. Click on **Add Token**. Provide a name and click on **Save**
6. Copy the API Token generated.
7. Keep this in a safe place, this value is later required in job_config.ini.

---

# 🛠️ Installation & Setup

Follow these quick steps to get your local environment up and running from the project root folder.

### 1. Create and Activate a Virtual Environment
It is highly recommended to use an isolated virtual environment to avoid version conflicts with other Python packages on your system.

* **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate

  ```

* **On Windows (Command Prompt):**
  ```cmd
    python -m venv venv
    call venv\Scripts\activate
 
  ```


* **On Windows (PowerShell):**
  ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1

  ```



### 2. Install Dependencies

Once your virtual environment is active (you should see `(venv)` at the beginning of your terminal line), install the required packages from the project root:

```bash
pip install .

```

---

# ⚙️ Configuration (`job_config.ini`)

Before running the application, you need to configure your settings. Update the file named `job_config.ini` in your **project root folder** and fill in your specific details:

```ini
[STORAGE]
# Absolute path to the directory where you want the store the data related to HelloBuddy.
APP_DATA_PATH = <ABSOLUTE_PATH_TO_DATA_DIRECTORY>

[EMAIL]
# Email address to which the report will be sent.
RECIPIENT = 

[SCHEDULER]
# The time of day you want the report generated and emailed (24-hour format HH:MM)
JOB_TIME = 13:54

[API_KEYS]
# Your official SerpApi API Key (Keep this secret!)
SERP_API_KEY = <YOUR_SERPAPI_KEY>
# Your official Mail Trap API Key (Keep this secret!)
MAILTRAP_API_TOKEN = < YOUR_MAILTRAP_API_TOKEN>
# Your official Reed API Key (Keep this secret!)
REED_API_KEY =
# Your official Adzuna API Key (Keep this secret!)
ADZUNA_APP_KEY =
# Your official Adzuna Appp Id (Keep this secret!)
ADZUNA_APP_ID =

[SEARCH_SETTINGS]
NUM_PAGES = 2
# The target job role (e.g., AI Architect, Python Developer) search query string specific to Serp Provider
SEARCH_QUERY_SERP =
# The target job role (e.g., AI Architect, Python Developer)
SEARCH_QUERY = <YOUR_JOB_SEARCH_QUERY>
# A valid geographic region or country matching the target market
SEARCH_LOCATION = <YOUR_JOB_SEARCH_LOCATION> # e.g., "New York, NY", "San Francisco, CA", etc.
# The two-letter country code matching your target market (e.g., in, us, uk)
SEARCH_COUNTRY = <YOUR_JOB_SEARCH_COUNTRY CODE>  # e.g., "us" for United States, "in" for India, etc.

```

---

# 🏃 Running the Application

With your virtual environment active and your `job_config.ini` completely filled out, kickstart the background worker by running the following command from the project root folder:

```bash
hellobuddy job-search

```

---

# 🤝 Happy Job Hunting!

Sit back, relax, and let **HelloBuddy** keep its eyes on the market for you. If you need to stop the scheduler at any time, simply press `CTRL + C` in your active terminal session.

```