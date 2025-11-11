from flask import Flask, render_template_string, request
import random
import logging

app = Flask(__name__)
app.secret_key = "boys"

# Very simple in-memory counter per IP
failed_captcha_attempts = {}

# Logging to file
logging.basicConfig(
    filename="security.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def generate_captcha():
    a, b = random.randint(1, 9), random.randint(1, 9)
    question = f"What is {a} + {b}?"
    answer = str(a + b)
    return question, answer

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Login with CAPTCHA</title></head>
<body>
  <h2>Login Page (Flask CAPTCHA Demo)</h2>

  {% if locked_out %}
    <p style="color:red; font-weight:bold;">
      🚫 Too many failed CAPTCHA attempts from your IP. Please wait before trying again.
    </p>
  {% endif %}

  <form method="POST">
    <label>Username:</label><br>
    <input type="text" name="username" {% if locked_out %}disabled{% endif %} required><br><br>

    <label>Password:</label><br>
    <input type="password" name="password" {% if locked_out %}disabled{% endif %} required><br><br>

    <label>Are you human? {{ question }}</label><br>
    <input type="text" name="captcha_answer" {% if locked_out %}disabled{% endif %} required><br><br>

    <input type="hidden" name="correct_answer" value="{{ answer }}">

    <button type="submit" {% if locked_out %}disabled{% endif %}>Login</button>
  </form>

  <p style="color: blue;">{{ message }}</p>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def login():
    client_ip = request.remote_addr or "unknown"

    # How many fails from this IP so far?
    count = failed_captcha_attempts.get(client_ip, 0)
    locked_out = count >= 3
    message = ""

    # New captcha each request
    question, answer = generate_captcha()

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # If already locked out, just show message and log it
        if locked_out:
            message = "🚫 Too many failed CAPTCHA attempts from your IP. Please wait before trying again."
            logging.warning(f"Blocked login (lockout) for user='{username}' from IP={client_ip}")
        else:
            user_answer = request.form["captcha_answer"]
            correct_answer = request.form["correct_answer"]

            if user_answer.strip() != correct_answer:
                # Increase counter for this IP
                count += 1
                failed_captcha_attempts[client_ip] = count

                locked_out = count >= 3

                if locked_out:
                    message = "🚫 Too many failed CAPTCHA attempts from your IP. Please wait before trying again."
                    logging.warning(f"CAPTCHA lockout for user='{username}' from IP={client_ip}")
                else:
                    message = "❌ CAPTCHA failed. Please try again."
                    logging.warning(f"Failed CAPTCHA for user='{username}' from IP={client_ip}")
            else:
                # CAPTCHA passed → reset counter for this IP
                failed_captcha_attempts[client_ip] = 0

                if username == "admin" and password == "password":
                    message = "✅ Login successful!"
                    logging.info(f"Successful login for user='{username}' from IP={client_ip}")
                else:
                    message = "⚠️ Invalid credentials."
                    logging.warning(f"Invalid credentials for user='{username}' from IP={client_ip}")

    return render_template_string(
        HTML_TEMPLATE,
        question=question,
        answer=answer,
        message=message,
        locked_out=locked_out,
    )

if __name__ == "__main__":
    # debug=True is fine; just don't edit the file while testing lockout,
    # because saving restarts the app and clears the counter.
    app.run(debug=True)
