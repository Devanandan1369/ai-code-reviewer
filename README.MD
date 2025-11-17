#  AI Code Review Bot

This project is a code review bot that uses AI to check your code.

You give it a link to a GitHub pull request, and it:
1.  Reads all the code changes (the "diff").
2.  Sends that code to an AI (Groq's LLaMA 3.1).
3.  The AI writes a review, looking for bugs, style issues, and ways to improve.
4.  It shows you the review on a simple web page.


##  How to Run This Project (The Easy Way)

The application is deployed at : 
https://ai-code-reviewer-mojd.onrender.com/


Also, you can setup it yourself as explained below:

This whole project is packed into "Docker," which means you can run all its different parts with one single command.

**You will need:**
* Docker Desktop (make sure it's installed and running).
* A Groq AI key (it's free, get one [here](https://console.groq.com/keys)).

---

### Step 1: Set Up Your Key

1.  Find the file `.env.example` in this folder.
2.  Make a copy of it and rename the copy to just `.env`.
3.  Open the new `.env` file and paste your secret Groq API key inside.

### Step 2: Run It!

Open your terminal in the project folder and run this one command:

```bash
docker-compose up --build
```

Your terminal will fill up with logs. This is normal! It's just all the parts starting up.

### Step 3: Use the App

Once the logs settle down, open your web browser and go to:

**`http://localhost:8501`**

You should see the app's web page, where you can paste a GitHub PR link to start your first review.

**To stop everything:** Go back to your terminal and press `Ctrl+C`.

---

##  How It All Works (The Details)

This project isn't just one app; it's four separate services that all talk to each other:

1.  **Streamlit (`ui`):** The friendly web page you see at `localhost:8501`.
2.  **FastAPI (`api`):** A "backend" server that takes orders from the web page.
3.  **Celery (`worker`):** The "heavy lifter." It takes the order from the API and does the actual work: fetching the code and talking to the AI.
4.  **Redis (`redis`):** A super-fast database that holds the "to-do" list and the final results.

`docker-compose` is the "conductor" that launches and connects all four of these services for you.

##  What's Next?

This project works great, but it could be even cooler. Here are some ideas:

* **Make it automatic:** Change it to a "GitHub Webhook" so it *automatically* reviews new pull requests as soon as they're created.
* **Better logging:** Switch from simple `print()` statements to a real logging system.
* **Use a real database:** Swap Redis for PostgreSQL to save all reviews permanently.
